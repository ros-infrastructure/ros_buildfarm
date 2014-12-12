import sys

from catkin_pkg.package import parse_package_string
from rosdistro import get_distribution_cache
from rosdistro import get_index

from ros_buildfarm.common import get_devel_view_name
from ros_buildfarm.common import git_github_orgunit
from ros_buildfarm.common import get_github_project_url
from ros_buildfarm.common \
    import get_repositories_and_script_generating_key_files
from ros_buildfarm.common import JobValidationError
from ros_buildfarm.config import get_distribution_file
from ros_buildfarm.config import get_index as get_config_index
from ros_buildfarm.config import get_source_build_files
from ros_buildfarm.git import get_repository_url
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_view
from ros_buildfarm.jenkins import connect
from ros_buildfarm.jenkins import remove_jobs
from ros_buildfarm.templates import expand_template


def configure_devel_jobs(
        config_url, rosdistro_name, source_build_name):
    """
    Configure all Jenkins devel jobs.

    L{configure_release_job} will be invoked for source repository and target
    which matches the build file criteria.
    """
    config = get_config_index(config_url)
    build_files = get_source_build_files(config, rosdistro_name)
    build_file = build_files[source_build_name]

    index = get_index(config.rosdistro_index_url)

    dist_cache = None
    if build_file.notify_maintainers:
        dist_cache = get_distribution_cache(index, rosdistro_name)

    # get targets
    targets = []
    for os_name in build_file.targets.keys():
        for os_code_name in build_file.targets[os_name].keys():
            for arch in build_file.targets[os_name][os_code_name]:
                targets.append((os_name, os_code_name, arch))
    print('The build file contains the following targets:')
    for os_name, os_code_name, arch in targets:
        print('  -', os_name, os_code_name, arch)

    dist_file = get_distribution_file(index, rosdistro_name, build_file)
    if not dist_file:
        print('No distribution file matches the build file')
        return

    jenkins = connect(config.jenkins_url)

    view_name = get_devel_view_name(rosdistro_name, source_build_name)
    view = configure_devel_view(jenkins, view_name)

    repo_names = dist_file.repositories.keys()
    repo_names = build_file.filter_repositories(repo_names)

    job_names = []
    for repo_name in sorted(repo_names):
        repo = dist_file.repositories[repo_name]
        if not repo.source_repository:
            print("Skipping repository '%s': no source section" % repo_name)
            continue
        if not repo.source_repository.version:
            print("Skipping repository '%s': no source version" % repo_name)
            continue

        job_types = []
        # check for testing commits
        if build_file.test_commits_force is False:
            print(("Skipping repository '%s': 'test_commits' is forced to " +
                   "false in the build file") % repo_name)
        elif repo.source_repository.test_commits is False:
            print(("Skipping repository '%s': 'test_commits' of the " +
                   "repository set to false") % repo_name)
        elif repo.source_repository.test_commits is None and \
                not build_file.test_commits_default:
            print(("Skipping repository '%s': 'test_commits' defaults to " +
                   "false in the build file") % repo_name)
        else:
            job_types.append('commit')
        # check for testing commits
        if build_file.test_pull_requests_force is False:
            # print(("Skipping repository '%s': 'test_pull_requests' is " +
            #        "forced to false in the build file") % repo_name)
            pass
        elif repo.source_repository.test_pull_requests is False:
            # print(("Skipping repository '%s': 'test_pull_requests' of the " +
            #        "repository set to false") % repo_name)
            pass
        elif repo.source_repository.test_pull_requests is None and \
                not build_file.test_pull_requests_default:
            # print(("Skipping repository '%s': 'test_pull_requests' " +
            #        "defaults to false in the build file") % repo_name)
            pass
        else:
            print("Pull request job for repository '%s'" % repo_name)
            job_types.append('pull_request')

        for job_type in job_types:
            pull_request = job_type == 'pull_request'
            for os_name, os_code_name, arch in targets:
                try:
                    job_name = configure_devel_job(
                        config_url, rosdistro_name, source_build_name,
                        repo_name, os_name, os_code_name, arch, pull_request,
                        config=config, build_file=build_file,
                        index=index, dist_file=dist_file,
                        dist_cache=dist_cache, jenkins=jenkins, view=view)
                    job_names.append(job_name)
                except JobValidationError as e:
                    print(e.message, file=sys.stderr)

    # delete obsolete jobs in this view
    remove_jobs(jenkins, '%s__' % view_name, job_names)


def configure_devel_job(
        config_url, rosdistro_name, source_build_name,
        repo_name, os_name, os_code_name, arch, pull_request,
        config=None, build_file=None,
        index=None, dist_file=None, dist_cache=None,
        jenkins=None, view=None):
    """
    Configure a single Jenkins devel job.

    This includes the following steps:
    - clone the source repository to use
    - clone the ros_buildfarm repository
    - write the distribution repository keys into files
    - invoke the release/run_devel_job.py script
    """
    if config is None:
        config = get_config_index(config_url)
    if build_file is None:
        build_files = get_source_build_files(config, rosdistro_name)
        build_file = build_files[source_build_name]

    if index is None:
        index = get_index(config.rosdistro_index_url)
    if dist_file is None:
        dist_file = get_distribution_file(index, rosdistro_name, build_file)
        if not dist_file:
            raise JobValidationError(
                'No distribution file matches the build file')

    repo_names = dist_file.repositories.keys()
    repo_names = build_file.filter_repositories(repo_names)

    if repo_name not in repo_names:
        raise JobValidationError(
            "Invalid repository name '%s' " % repo_name +
            'choose one of the following: %s' % ', '.join(sorted(repo_names)))

    repo = dist_file.repositories[repo_name]

    if not repo.source_repository:
        raise JobValidationError(
            "Repository '%s' has no source section" % repo_name)
    if not repo.source_repository.version:
        raise JobValidationError(
            "Repository '%s' has no source version" % repo_name)

    if os_name not in build_file.targets.keys():
        raise JobValidationError(
            "Invalid OS name '%s' " % os_name +
            'choose one of the following: ' +
            ', '.join(sorted(build_file.targets.keys())))
    if os_code_name not in build_file.targets[os_name].keys():
        raise JobValidationError(
            "Invalid OS code name '%s' " % os_code_name +
            'choose one of the following: ' +
            ', '.join(sorted(build_file.targets[os_name].keys())))
    if arch not in build_file.targets[os_name][os_code_name]:
        raise JobValidationError(
            "Invalid architecture '%s' " % arch +
            'choose one of the following: %s' % ', '.join(sorted(
                build_file.targets[os_name][os_code_name])))

    if dist_cache is None and build_file.notify_maintainers:
        dist_cache = get_distribution_cache(index, rosdistro_name)
    if jenkins is None:
        jenkins = connect(config.jenkins_url)
    if view is None:
        view_name = get_devel_view_name(rosdistro_name, source_build_name)
        configure_devel_view(jenkins, view_name)

    job_name = get_devel_job_name(
        rosdistro_name, source_build_name,
        repo_name, os_name, os_code_name, arch, pull_request)

    job_config = _get_devel_job_config(
        config, rosdistro_name, source_build_name,
        build_file, os_name, os_code_name, arch, repo.source_repository,
        repo_name, pull_request, job_name, dist_cache=dist_cache)
    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object) and jenkins is not False:
        configure_job(jenkins, job_name, job_config)

    return job_name


def get_devel_job_name(rosdistro_name, source_build_name,
                       repo_name, os_name, os_code_name, arch,
                       pull_request=False):
    view_name = get_devel_view_name(rosdistro_name, source_build_name)
    job_name = '%s__%s__%s_%s_%s' % \
        (view_name, repo_name, os_name, os_code_name, arch)
    if pull_request:
        job_name += '__pull_request'
    return job_name


def configure_devel_view(jenkins, view_name):
    return configure_view(
        jenkins, view_name, include_regex='%s__.+' % view_name)


def _get_devel_job_config(
        config, rosdistro_name, source_build_name,
        build_file, os_name, os_code_name, arch, source_repo_spec,
        repo_name, pull_request, job_name, dist_cache=None):
    template_name = 'devel/devel_job.xml.em'

    repository_args, script_generating_key_files = \
        get_repositories_and_script_generating_key_files(config, build_file)

    maintainer_emails = set([])
    if build_file.notify_maintainers and dist_cache:
        # add maintainers listed in latest release to recipients
        repo = dist_cache.distribution_file.repositories[repo_name]
        if repo.release_repository:
            for pkg_name in repo.release_repository.package_names:
                if pkg_name not in dist_cache.release_package_xmls:
                    continue
                pkg_xml = dist_cache.release_package_xmls[pkg_name]
                pkg = parse_package_string(pkg_xml)
                for m in pkg.maintainers:
                    maintainer_emails.add(m.email)

    job_priority = \
        build_file.jenkins_commit_job_priority \
        if not pull_request \
        else build_file.jenkins_pull_request_job_priority

    job_data = {
        'github_url': get_github_project_url(source_repo_spec.url),

        'job_priority': job_priority,

        'pull_request': pull_request,

        'source_repo_spec': source_repo_spec,

        # this should not be necessary
        'job_name': job_name,

        'github_orgunit': git_github_orgunit(source_repo_spec.url),

        'ros_buildfarm_url': get_repository_url(),

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_index_url': config.rosdistro_index_url,
        'rosdistro_name': rosdistro_name,
        'source_build_name': source_build_name,
        'os_name': os_name,
        'os_code_name': os_code_name,
        'arch': arch,
        'repository_args': repository_args,

        'notify_emails': set(config.notify_emails + build_file.notify_emails),
        'maintainer_emails': maintainer_emails,
        'notify_maintainers': build_file.notify_maintainers,
        'notify_committers': build_file.notify_committers,

        'timeout_minutes': build_file.jenkins_job_timeout,
    }
    job_config = expand_template(template_name, job_data)
    return job_config
