# Copyright 2020 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
import time

from pulpcore.client import pulp_rpm
from pulpcore.client import pulpcore


def format_pkg_ver(pkg):
    return '%s%s-%s' % (
        (pkg.epoch + ':') if pkg.epoch != '0' else '',
        pkg.version,
        pkg.release)


def _enumerate_recursive_dependencies(packages, target_names):
    new_names = set(target_names)

    while new_names:
        target_names = new_names
        new_names = set()
        for pkg in packages:
            if target_names.intersection(req[0] for req in pkg.requires):
                yield (pkg.pulp_href, pkg)
                new_names.add(pkg.name)
                new_names.update(prov[0] for prov in pkg.provides)


class PulpPageIterator:

    def __init__(self, fetch_function, *args, **kwargs):  # noqa: D107
        self._get_next = lambda offset: fetch_function(*args, **kwargs, offset=offset)
        self._offset = 0
        self._next_page()

    def _next_page(self):
        self._page = self._get_next(self._offset)
        self._offset += len(self._page.results)
        self._iter = iter(self._page.results)

    def __iter__(self):
        return self

    def __len__(self):
        return self._page.count

    def __next__(self):
        try:
            return next(self._iter)
        except StopIteration:
            if not self._page.next:
                raise

        self._next_page()
        return next(self._iter)


class PulpRpmClient:

    def __init__(
            self, base_url, username, password,
            task_timeout=60.0, task_polling_interval=0.5):  # noqa: D107
        self._task_timeout = task_timeout
        self._task_polling_interval = task_polling_interval

        self._config = pulpcore.Configuration(
            base_url, username=username, password=password)

        # https://pulp.plan.io/issues/5932
        self._config.safe_chars_for_path_param = '/'

        # Core APIs
        self._core_client = pulpcore.ApiClient(self._config)
        self._core_tasks_api = pulpcore.TasksApi(self._core_client)

        # RPM APIs
        self._rpm_client = pulp_rpm.ApiClient(self._config)
        self._rpm_distributions_api = pulp_rpm.DistributionsRpmApi(self._rpm_client)
        self._rpm_packages_api = pulp_rpm.ContentPackagesApi(self._rpm_client)
        self._rpm_publications_api = pulp_rpm.PublicationsRpmApi(self._rpm_client)
        self._rpm_remotes_api = pulp_rpm.RemotesRpmApi(self._rpm_client)
        self._rpm_repos_api = pulp_rpm.RepositoriesRpmApi(self._rpm_client)

    def _wait_for_task(self, task_href):
        task = self._core_tasks_api.read(task_href)

        timeout = self._task_timeout
        while task.state != 'completed':
            if task.state in ['failed', 'canceled']:
                raise RuntimeError(
                    "Pulp task '%s' did not complete (%s)" % (task.pulp_href, task.state))
            time.sleep(self._task_polling_interval)
            timeout -= self._task_polling_interval
            if timeout <= 0:
                task_cancel = pulpcore.TaskCancel('canceled')
                task = self._core_tasks_api.tasks_cancel(task.pulp_href, task_cancel)
                if task.state != 'completed':
                    raise RuntimeError(
                        "Pulp task '%s' did not complete (timed out)" % task.pulp_href)

            task = self._core_tasks_api.read(task.pulp_href)

        return task

    def _publish_and_distribute(self, distribution, repo_version_href):
        # Publish the new version
        publish_data = pulp_rpm.RpmRpmPublication(repository_version=repo_version_href)
        publish_task_href = self._rpm_publications_api.create(publish_data).task
        publish_task = self._wait_for_task(publish_task_href)

        # Distribute the publication at the original endpoint
        distribution.publication = publish_task.created_resources[0]
        distribute_task_href = self._rpm_distributions_api.partial_update(
            distribution.pulp_href, distribution).task
        self._wait_for_task(distribute_task_href)

    def enumerate_distributions(self):
        return PulpPageIterator(
            self._rpm_distributions_api.list)

    def enumerate_pkgs_in_distribution_name(self, distribution_name):
        distribution = self._rpm_distributions_api.list(
            name=distribution_name).results[0]
        publication = self._rpm_publications_api.read(distribution.publication)
        return self.enumerate_pkgs_in_repo_ver(publication.repository_version)

    def enumerate_pkgs_in_repo_ver(self, repo_ver_href):
        return PulpPageIterator(
            self._rpm_packages_api.list, repository_version=repo_ver_href)

    def enumerate_remotes(self):
        return PulpPageIterator(self._rpm_remotes_api.list)

    def import_and_invalidate(
            self, distribution_name, packages_to_add,
            invalidate_expression, invalidate_downstream, package_cache=None, dry_run=False):
        distribution = self._rpm_distributions_api.list(
            name=distribution_name).results[0]
        old_publication = self._rpm_publications_api.read(distribution.publication)

        # Get the current packages
        current_pkgs = {
            pkg.pulp_href: pkg for pkg in
            self.enumerate_pkgs_in_repo_ver(old_publication.repository_version)}

        # Set up the package chache
        package_cache = {**(package_cache or {}), **current_pkgs}

        # Get the packages we're adding
        new_pkgs = {
            pkg.pulp_href: pkg for pkg in
            [package_cache.get(pkg_href) or self._rpm_packages_api.read(pkg_href)
                for pkg_href in packages_to_add]}

        # Invalidate packages
        pkgs_to_remove = {}
        new_pkg_names = set([pkg.name for pkg in new_pkgs.values()])
        # 1. Remove packages with the same name
        pkgs_to_remove.update({
            pkg.pulp_href: pkg for pkg in current_pkgs.values()
            if pkg.name in new_pkg_names})
        # 2. Remove downstream packages
        if invalidate_downstream:
            new_pkg_provides = new_pkg_names.union(
                prov[0] for pkg in new_pkgs.values() for prov in pkg.provides)
            pkgs_to_remove.update(
                _enumerate_recursive_dependencies(current_pkgs.values(), new_pkg_provides))
        # 3. Remove packages matching the invalidation expression
        if invalidate_expression:
            compiled_expression = re.compile(invalidate_expression)
            for pkg in current_pkgs.values():
                if compiled_expression.match(pkg.name):
                    pkgs_to_remove[pkg.pulp_href] = pkg

        # Prune the list of packages to add and remove
        # 1. Packages being added *always* end up in the repo
        for href_to_add in new_pkgs.keys():
            pkgs_to_remove.pop(href_to_add, None)
        # 2. Packages being added don't need to get re-added
        for href_in_current in current_pkgs.keys():
            new_pkgs.pop(href_in_current, None)

        if dry_run:
            return (new_pkgs.values(), pkgs_to_remove.values())

        # Commit the changes
        mod_data = pulp_rpm.RepositoryAddRemoveContent(
            add_content_units=list(new_pkgs.keys()),
            remove_content_units=list(pkgs_to_remove.keys()),
            base_version=old_publication.repository_version)
        mod_task_href = self._rpm_repos_api.modify(old_publication.repository, mod_data).task
        mod_task = self._wait_for_task(mod_task_href)

        if mod_task.created_resources:
            self._publish_and_distribute(distribution, mod_task.created_resources[0])

        return (new_pkgs.values(), pkgs_to_remove.values())

    def mirror_remote_to_distribution(self, remote_name, distribution_name, dry_run=False):
        remote = self._rpm_remotes_api.list(name=remote_name).results[0]
        distribution = self._rpm_distributions_api.list(name=distribution_name).results[0]
        old_publication = self._rpm_publications_api.read(distribution.publication)

        sync_data = pulp_rpm.RepositorySyncURL(
            remote=remote.pulp_href,
            mirror=True)

        if dry_run:
            return

        sync_task_href = self._rpm_repos_api.sync(old_publication.repository, sync_data).task
        sync_task = self._wait_for_task(sync_task_href)

        if sync_task.created_resources:
            self._publish_and_distribute(distribution, sync_task.created_resources[0])

    def upload_pkg(self, file_path):
        relative_path = os.path.basename(file_path)
        upload_task_href = self._rpm_packages_api.create(
            relative_path, file=file_path).task
        upload_task = self._wait_for_task(upload_task_href)

        return self._rpm_packages_api.read(upload_task.created_resources[0])
