# Copyright 2014-2016 Open Source Robotics Foundation, Inc.
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

from __future__ import print_function

import copy
import difflib
import sys
from xml.etree import ElementTree

from jenkinsapi.jenkins import Jenkins
from jenkinsapi.views import Views

try:
    from jenkinsapi.utils.crumb_requester import CrumbRequester
except ImportError:
    from .crumb_requester import CrumbRequester
from .jenkins_credentials import get_credentials
from .templates import expand_template

JENKINS_MANAGEMENT_VIEW = 'Manage'


class JenkinsProxy(Jenkins):
    """Proxy for Jenkins instance caching data for performance reasons."""

    def __init__(self, *args, **kwargs):  # noqa: D107
        requester_kwargs = copy.copy(kwargs)
        requester_kwargs['baseurl'] = args[0]
        kwargs['requester'] = CrumbRequester(**requester_kwargs)
        super(JenkinsProxy, self).__init__(*args, **kwargs)
        self.__jobs = None

    @property
    def jobs(self):
        if self.__jobs is None:
            self.__jobs = super(JenkinsProxy, self).jobs
        return self.__jobs


_cached_jenkins = None


def connect(jenkins_url):
    global _cached_jenkins
    if _cached_jenkins and _cached_jenkins.base_server_url() == jenkins_url:
        print("Reusing connection to Jenkins '%s'" % jenkins_url)
        return _cached_jenkins

    print("Connecting to Jenkins '%s'" % jenkins_url)
    username, password = get_credentials(jenkins_url)
    jenkins = JenkinsProxy(jenkins_url, username=username, password=password)
    print("Connected to Jenkins version '%s'" % jenkins.version)
    _cached_jenkins = jenkins
    return jenkins


def configure_management_view(jenkins, dry_run=False):
    return configure_view(
        jenkins, JENKINS_MANAGEMENT_VIEW, include_regex='^((?!__).)*$',
        dry_run=dry_run)


_cached_views = {}


def configure_view(
        jenkins, view_name, include_regex=None, filter_queue=True,
        template_name='generic_view.xml.em', dry_run=False, context_lines=0):
    global _cached_views
    key = (view_name, include_regex, filter_queue, template_name, dry_run)
    if key in _cached_views:
        print("Skipped view '%s' as it has been configured before" % view_name)
        return _cached_views[key]

    view_config = get_view_config(
        template_name, view_name, include_regex=include_regex,
        filter_queue=filter_queue)
    if not jenkins:
        _cached_views[key] = view_config
        return view_config
    view_type = _get_view_type(view_config)
    create_view = view_name not in jenkins.views
    dry_run_suffix = ' (dry run)' if dry_run else ''
    if create_view:
        print(
            "Creating view '%s' of type '%s'%s" %
            (view_name, view_type, dry_run_suffix))
        view = jenkins.views.create(view_name, view_type=view_type) \
            if not dry_run else None
        remote_view_config = view.get_config() \
            if view is not None else None
    else:
        print("Ensure that view '%s' exists" % view_name)
        view = jenkins.views[view_name]
        remote_view_config = view.get_config()
        remote_view_type = _get_view_type(remote_view_config)
        if remote_view_type != view_type:
            del jenkins.views[view_name]
            print(
                "Recreating view '%s' of type '%s'%s" %
                (view_name, view_type, dry_run_suffix))
            view = jenkins.views.create(view_name, view_type=view_type) \
                if not dry_run else None
            remote_view_config = view.get_config() \
                if view is not None else None

    if not remote_view_config:
        print(
            'Can not produce diff during dry run if the view is new or of '
            'different type', file=sys.stderr)
        return None

    diff = _diff_configs(remote_view_config, view_config, context_lines)
    # evaluate generator since it might yield no values
    diff = list(diff)
    if not diff:
        print("Skipped '%s' because the config is the same%s" %
              (view_name, dry_run_suffix))
    else:
        print("Updating view '%s'%s" % (view_name, dry_run_suffix))
        if not create_view:
            print('   ', '<<<')
            for line in diff:
                print('   ', line.rstrip('\n'))
            print('   ', '>>>')
        try:
            response_text = view.update_config(view_config) \
                if not dry_run else None
        except Exception:
            print("Failed to configure view '%s' with config:\n%s" %
                  (view_name, view_config), file=sys.stderr)
            raise
        if response_text:
            raise RuntimeError(
                "Failed to configure view '%s':\n%s" %
                (view_name, response_text))
    _cached_views[key] = view
    return view


def get_view_config(
        template_name, view_name, include_regex=None, filter_queue=True,
        data=None):
    view_data = copy.deepcopy(data) if data is not None else {}
    view_data.update({
        'view_name': view_name,
        'include_regex': include_regex,
        'filter_queue': filter_queue,
    })
    view_config = expand_template(template_name, view_data)
    return view_config


def _get_view_type(view_config):
    root = ElementTree.fromstring(view_config)
    root.tag
    if root.tag == 'hudson.model.ListView':
        return Views.LIST_VIEW
    if root.tag == 'hudson.plugins.view.dashboard.Dashboard':
        return Views.DASHBOARD_VIEW
    assert False, 'Unknown list type: ' + root.tag


_cached_jobs = {}


def configure_job(jenkins, job_name, job_config, view=None, dry_run=False, context_lines=0):
    global _cached_jobs
    key = (job_name, job_config, view, dry_run)
    if key in _cached_jobs:
        print("Skipped job '%s' as it has been configured before" % job_name)
        return _cached_jobs[key]

    dry_run_suffix = ' (dry run)' if dry_run else ''
    response_text = None
    try:
        if not jenkins.has_job(job_name):
            print("Creating job '%s'%s" % (job_name, dry_run_suffix))
            job = jenkins.create_job(job_name, job_config) \
                if not dry_run else None
        else:
            job = jenkins.get_job(job_name)
            remote_job_config = job.get_config()
            diff = _diff_configs(remote_job_config, job_config, context_lines)
            # evaluate generator since it might yield no values
            diff = list(diff)
            if not diff:
                print("Skipped '%s' because the config is the same%s" %
                      (job_name, dry_run_suffix))
            else:
                print("Updating job '%s'%s" % (job_name, dry_run_suffix))
                print('   ', '<<<')
                for line in diff:
                    print('   ', line.rstrip('\n'))
                print('   ', '>>>')
                response_text = job.update_config(job_config) \
                    if not dry_run else None
                if response_text:
                    print('Failed to update job config:\n%s' % response_text)
                    raise RuntimeError()
    except Exception:
        print("Failed to configure job '%s' with config:\n%s" %
              (job_name, job_config), file=sys.stderr)
        raise
    if response_text:
        raise RuntimeError(
            "Failed to configure job '%s':\n%s" % (job_name, response_text))
    if view is not None:
        if job_name not in view:
            print(
                "Adding job '%s' to view '%s'%s" %
                (job_name, view.name, dry_run_suffix))
            job = view.add_job(job_name, job) \
                if not dry_run else job
        else:
            print("Job '%s' is already in view '%s'" % (job_name, view.name))
    _cached_jobs[key] = job
    return job


def invoke_job(jenkins, job_name, cause=None):
    try:
        if not jenkins.has_job(job_name):
            print("Failed to invoke job '%s' because it does not exist" %
                  job_name, file=sys.stderr)
            return False

        job = jenkins.get_job(job_name)
        if not job.is_enabled():
            print("Failed to invoke job '%s' because it is disabled" %
                  job_name, file=sys.stderr)
            return False
        if job.is_queued():
            print("Skipped to invoke job '%s' because it is queued" %
                  job_name, file=sys.stderr)
            return False
        if job.is_running():
            print("Skipped to invoke job '%s' because it is running" %
                  job_name, file=sys.stderr)
            return False
        print("Invoking job '%s'" % job_name)
        job.invoke(cause=cause)
    except Exception:
        print("Failed to invoke job '%s'" % job_name, file=sys.stderr)
        raise
    return True


def _diff_configs(remote_config, new_config, context_lines):
    remote_root = ElementTree.fromstring(remote_config)
    new_root = ElementTree.fromstring(new_config)

    # ignore description which contains timestamp
    if remote_root.find('description') is not None:
        remote_root.find('description').text = ''
    if new_root.find('description') is not None:
        new_root.find('description').text = ''

    if ElementTree.tostring(remote_root) == ElementTree.tostring(new_root):
        return []

    encoding_type = 'utf-8' if sys.version_info[0] < 3 else 'unicode'
    xml1 = ElementTree.tostring(remote_root, encoding=encoding_type)
    xml2 = ElementTree.tostring(new_root, encoding=encoding_type)
    lines1 = xml1.splitlines()
    lines2 = xml2.splitlines()

    return difflib.unified_diff(
        lines1, lines2, 'remote config', 'new config', n=context_lines)


def remove_jobs(jenkins, job_prefix, excluded_job_names, dry_run=False):
    dry_run_suffix = ' (dry run)' if dry_run else ''
    for job_name in jenkins.jobs.keys():
        if not job_name.startswith(job_prefix):
            continue
        if job_name in excluded_job_names:
            continue
        print("Deleting job '%s'%s" % (job_name, dry_run_suffix))
        if dry_run:
            continue
        jenkins.delete_job(job_name)
