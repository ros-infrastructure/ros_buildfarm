"""
Documentation and functions for devel jobs.

The script ``scripts/devel/generate_devel_maintenance_jobs.py`` generates Jenkins jobs
for each repository and os_name/os_code_name/arch matching the build file.

It requires the following arguments to identify the build file:
  --rosdistro-index-url
  --rosdistro-name
  --source-build-name

The job configuration contains a build step to:
  write all keys to files
  clones the following repositories:
    ros_buildfarm
    SOURCE repository to run CI on
  invokes
    scripts/devel/run_devel_job.py
      --distribution-repository-urls
      --distribution-repository-key-files

Each devel Jenkins job is expanded from the template
  templates/devel/devel_job.xml.em
It clones the following repositories:
  ros_buildfarm
  SOURCE repository to run CI on
It then invokes
  scripts/devel/run_devel_job.py
    which expands a Dockerfile from templates/devel/devel_create_tasks.Dockerfile.em
"""

from datetime import datetime

from rosdistro import get_distribution_file
from rosdistro import get_index
from rosdistro import get_index_url
from rosdistro import get_source_build_files

from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_view
from ros_buildfarm.jenkins import connect
from ros_buildfarm.templates import expand_template


def add_arguments_for_source_build_file(parser):
    parser.add_argument(
        '--rosdistro-index-url',
        default=get_index_url(),
        help=("The URL to the ROS distro index (default: '%s', based on the " +
              "environment variable ROSDISTRO_INDEX_URL") % get_index_url())
    parser.add_argument(
        'rosdistro_name',
        help="The name of the ROS distro from the index")
    parser.add_argument(
        'source_build_name',
        help="The name of the 'source-build' file from the index")


def add_arguments_for_target(parser):
    add_arguments_for_source_build_file(parser)
    parser.add_argument(
        'repository_name',
        help="The name of the 'repository' from the distribution file")
    parser.add_argument(
        'os_name',
        help="The OS name from the 'source-build' file")
    parser.add_argument(
        'os_code_name',
        help="A OS code name from the 'source-build' file")
    parser.add_argument(
        'arch',
        help="An arch from the 'source-build' file")


# For every source repository and target which matches the build file criteria
# invoke configure_devel_job().
def configure_devel_jobs(
        rosdistro_index_url, rosdistro_name, source_build_name):
    index = get_index(rosdistro_index_url)
    build_files = get_source_build_files(index, rosdistro_name)
    build_file = build_files[source_build_name]

    # get targets
    targets = []
    for os_name in build_file.get_target_os_names():
        for os_code_name in build_file.get_target_os_code_names(os_name):
            for arch in build_file.get_target_arches(os_name, os_code_name):
                targets.append((os_name, os_code_name, arch))
    print('The build file contains the following targets:')
    for os_name, os_code_name, arch in targets:
        print('  -', os_name, os_code_name, arch)

    dist_file = get_distribution_file(index, rosdistro_name)

    jenkins = connect(build_file.jenkins_url)

    view_name = _get_devel_view_name(rosdistro_name, source_build_name)
    view = configure_view(jenkins, view_name)

    repo_names = dist_file.repositories.keys()
    repo_names = build_file.filter_repositories(repo_names)

    for repo_name in sorted(repo_names):
        repo = dist_file.repositories[repo_name]
        if not repo.source_repository:
            print("Skipping repository '%s': no source section" % repo_name)
            continue
        if not repo.source_repository.version:
            print("Skipping repository '%s': no source version" % repo_name)
            continue

        for os_name, os_code_name, arch in targets:
            configure_devel_job(
                rosdistro_index_url, rosdistro_name, source_build_name,
                repo_name, os_name, os_code_name, arch,
                index=index, build_file=build_file, dist_file=dist_file,
                jenkins=jenkins, view=view)


# Configure a Jenkins devel job which
# - clones the source repository to use
# - clones the ros_buildfarm repository
# - writes the distribution repository keys into files
# - invokes the run_devel_job script
def configure_devel_job(
        rosdistro_index_url, rosdistro_name, source_build_name,
        repo_name, os_name, os_code_name, arch,
        index=None, build_file=None, dist_file=None,
        jenkins=None, view=None):
    if index is None:
        index = get_index(rosdistro_index_url)
    if build_file is None:
        build_files = get_source_build_files(index, rosdistro_name)
        build_file = build_files[source_build_name]
    if dist_file is None:
        dist_file = get_distribution_file(index, rosdistro_name)

    repo_names = dist_file.repositories.keys()
    repo_names = build_file.filter_repositories(repo_names)

    if repo_name not in repo_names:
        return "Invalid repository name '%s' " % repo_name + \
            'choose one of the following: ' + \
            ', '.join(sorted(dist_file.repositories.keys()))

    repo = dist_file.repositories[repo_name]

    if not repo.source_repository:
        return "Repository '%s' has no source section" % repo_name
    if not repo.source_repository.version:
        return "Repository '%s' has no source version" % repo_name

    if os_name not in build_file.get_target_os_names():
        return "Invalid OS name '%s' " % os_name + \
            'choose one of the following: ' + \
            ', '.join(sorted(build_file.get_target_os_names()))
    if os_code_name not in build_file.get_target_os_code_names(os_name):
        return "Invalid OS code name '%s' " % os_code_name + \
            'choose one of the following: ' + \
            ', '.join(sorted(build_file.get_target_os_code_names(os_name)))
    if arch not in build_file.get_target_arches(os_name, os_code_name):
        return "Invalid architecture '%s' " % arch + \
            'choose one of the following: ' + \
            ', '.join(sorted(
                build_file.get_target_arches(os_name, os_code_name)))

    conf = build_file.get_target_configuration(
        os_name=os_name, os_code_name=os_code_name, arch=arch)

    if jenkins is None:
        jenkins = connect(build_file.jenkins_url)
    if view is None:
        view_name = _get_devel_view_name(rosdistro_name, source_build_name)
        view = configure_view(jenkins, view_name)

    job_name = get_devel_job_name(
        rosdistro_name, source_build_name,
        repo_name, os_name, os_code_name, arch)

    job_config = _get_devel_job_config(
        rosdistro_index_url, rosdistro_name, source_build_name,
        build_file, os_name, os_code_name, arch, conf, repo.source_repository)
    # jenkinsapi.jenkins.Jenkins evaluates to false if job count is zero
    if isinstance(jenkins, object):
        configure_job(jenkins, job_name, job_config, view)


def _get_devel_view_name(rosdistro_name, source_build_name):
    return '%sdev%s' % (rosdistro_name[0].upper(), source_build_name)


def get_devel_job_name(rosdistro_name, source_build_name,
                       repo_name, os_name, os_code_name, arch):
    view_name = _get_devel_view_name(rosdistro_name, source_build_name)
    return '%s_%s__%s_%s_%s' % \
        (view_name, repo_name, os_name, os_code_name, arch)


def _get_devel_job_config(
        rosdistro_index_url, rosdistro_name, source_build_name,
        build_file, os_name, os_code_name, arch, conf, source_repo_spec):
    template_name = 'devel/devel_job.xml.em'
    now = datetime.utcnow()
    now_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    # extract the distribution repository urls and keys from the build file
    # and pass them as command line arguments and files
    # so that the job must not parse the build file
    apt_mirror_args = []
    script_generating_key_files = []
    if 'apt_mirrors' in conf:
        apt_mirrors = conf['apt_mirrors']
        if apt_mirrors:
            apt_mirror_args.append('--distribution-repository-urls')
            apt_mirror_args += apt_mirrors
    if 'apt_mirror_keys' in conf:
        apt_mirror_keys = conf['apt_mirror_keys']
        if apt_mirror_keys:
            apt_mirror_args.append('--distribution-repository-key-files')
            script_generating_key_files.append("mkdir -p $WORKSPACE/keys")
            script_generating_key_files.append("rm -fr $WORKSPACE/keys/*")
            for i, apt_mirror_key in enumerate(apt_mirror_keys):
                apt_mirror_args.append('$WORKSPACE/keys/%d.key' % i)
                script_generating_key_files.append(
                    'echo "%s" > $WORKSPACE/keys/%d.key' % (apt_mirror_key, i)
                )

    job_data = {
        'template_name': template_name,
        'now_str': now_str,

        'job_priority': build_file.jenkins_job_priority,

        'source_repo_spec': source_repo_spec,

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_index_url': rosdistro_index_url,
        'rosdistro_name': rosdistro_name,
        'source_build_name': source_build_name,
        'source_repo_spec': source_repo_spec,
        'os_name': os_name,
        'os_code_name': os_code_name,
        'arch': arch,
        'apt_mirror_args': apt_mirror_args,

        'recipients': build_file.notify_emails,

        'timeout_minutes': build_file.jenkins_job_timeout,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


# The script must run on a clean slave without installing anything
# therefore it creates a Dockerfile
# and runs all computations in the container
def run_devel_job(
        rosdistro_index_url, rosdistro_name, source_build_name,
        repo_name, os_name, os_code_name, arch,
        distribution_repository_urls, distribution_repository_key_files,
        workspace_root, dockerfile_dir):
    pass
