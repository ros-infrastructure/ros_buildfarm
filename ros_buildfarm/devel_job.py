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
from rosdistro import get_source_build_files

from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_view
from ros_buildfarm.jenkins import connect
from ros_buildfarm.templates import expand_template
from ros_buildfarm.templates import get_scm_snippet


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

    view = _get_devel_view(rosdistro_name, source_build_name, jenkins)

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

        # TODO
        if repo_name not in ['ros_tutorials', 'roscpp_core']:
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
    if jenkins is None:
        jenkins = connect(build_file.jenkins_url)
    if view is None:
        view = _get_devel_view(rosdistro_name, source_build_name, jenkins)

    repo = dist_file.repositories[repo_name]

    assert repo.source_repository, \
        "Repository '%s' has no source section" % repo_name
    assert repo.source_repository.version, \
        "Repository '%s' has no source version" % repo_name

    conf = build_file.get_target_configuration(
        os_name=os_name, os_code_name=os_code_name, arch=arch)

    job_name = '%s_%s__%s_%s_%s' % \
        (view.name, repo_name, os_name, os_code_name, arch)
    job_config = _get_devel_job_config(
        rosdistro_index_url, rosdistro_name, source_build_name,
        build_file, os_name, os_code_name, arch, conf, repo.source_repository)
    configure_job(jenkins, job_name, job_config, view)


def _get_devel_view(rosdistro_name, source_build_name, jenkins):
    view_name = '%sdev%s' % (rosdistro_name[0].upper(), source_build_name)
    return configure_view(jenkins, view_name)


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
        'description': "Generated at %s from template '%s'" %
        (now_str, template_name),
        '-LOG_ROTATOR': expand_template('snippet/log-rotator.xml.em', {
            'days_to_keep': 100,
            'num_to_keep': 100,
        }),
        '-PROPERTIES': expand_template(
            'snippet/property_job-priority.xml.em', {
                'priority': 3,
            }
        ),
        '-SCM': get_scm_snippet(
            source_repo_spec,
            'catkin_workspace/src/%s' % source_repo_spec.name),
        '-TRIGGERS': expand_template('snippet/trigger_poll.xml.em', {
            'spec': 'H * * * *'
        }),
        '-BUILDERS': expand_template('snippet/builder_shell.xml.em', {
            'script': '\n'.join([
                # TODO remove temporary checkout of rosdistro and dependency installation
                'echo "# BEGIN SECTION: Clone custom rosdistro"',
                'rm -fr rosdistro',
                'git clone https://github.com/dirk-thomas/ros-infrastructure_rosdistro.git rosdistro',
                'echo "# END SECTION"',
                '',
                'echo "# BEGIN SECTION: Clone ros_buildfarm"',
                'rm -fr ros_buildfarm',
                'git clone https://github.com/dirk-thomas/ros_buildfarm.git ros_buildfarm',
                'echo "# END SECTION"',
            ]),
        }) + expand_template('snippet/builder_shell.xml.em', {
            'script': '\n'.join([
                '# generate key files',
                'echo "# BEGIN SECTION: Generate key files"',
            ] + script_generating_key_files + [
                'echo "# END SECTION"',
            ]),
        }) + expand_template('snippet/builder_shell.xml.em', {
            'script': '\n'.join([
                '# generate Dockerfile, build and run it',
                '# generating the Dockerfiles for the actual build tasks',
                'echo "# BEGIN SECTION: Generate Dockerfile 1"',
                'mkdir -p $WORKSPACE/docker_generating_devel_dockers',
                'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
                '$WORKSPACE/ros_buildfarm/scripts/devel/run_devel_job.py' +
                ' --rosdistro-index-url %s' % rosdistro_index_url +
                ' --rosdistro-name %s' % rosdistro_name +
                ' --source-build-name %s' % source_build_name +
                ' --repo-name %s' % source_repo_spec.name +
                ' --os-name %s' % os_name +
                ' --os-code-name %s' % os_code_name +
                ' --arch %s' % arch +
                ' ' + ' '.join(apt_mirror_args) +
                ' --workspace-root $WORKSPACE/catkin_workspace' +
                ' --dockerfile-dir $WORKSPACE/docker_generating_devel_dockers',
                'echo "# END SECTION"',
                '',
                'echo "# BEGIN SECTION: Build Dockerfile - generating docker tasks"',
                'cd $WORKSPACE/docker_generating_devel_dockers',
                'docker.io build -t devel .',
                'echo "# END SECTION"',
                '',
                'echo "# BEGIN SECTION: Run Dockerfile - generating docker tasks"',
                'mkdir -p $WORKSPACE/docker_build_and_install',
                'mkdir -p $WORKSPACE/docker_build_and_test',
                'docker.io run' +
                ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm' +
                ' -v $WORKSPACE/catkin_workspace:/tmp/catkin_workspace' +
                ' -v $WORKSPACE/docker_build_and_install:/tmp/docker_build_and_install' +
                ' -v $WORKSPACE/docker_build_and_test:/tmp/docker_build_and_test' +
                ' devel',
                'echo "# END SECTION"',
            ]),
        }) + expand_template('snippet/builder_shell.xml.em', {
            'script': '\n'.join([
                'echo "# BEGIN SECTION: Build Dockerfile - build and install"',
                '# build and run build_and_install Dockerfile',
                'cd $WORKSPACE/docker_build_and_install',
                'docker.io build -t build_and_install .',
                'echo "# END SECTION"',
                '',
                'echo "# BEGIN SECTION: Run Dockerfile - build and install"',
                'ls -al $WORKSPACE/ros_buildfarm/scripts/command',
                'docker.io run' +
                ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm' +
                ' -v $WORKSPACE/catkin_workspace:/tmp/catkin_workspace' +
                ' build_and_install',
                'echo "# END SECTION"',
            ]),
        }) + expand_template('snippet/builder_shell.xml.em', {
            'script': '\n'.join([
                'echo "# BEGIN SECTION: Build Dockerfile - build and test"',
                '# build and run build_and_test Dockerfile',
                'cd $WORKSPACE/docker_build_and_test',
                'docker.io build -t build_and_test .',
                'echo "# END SECTION"',
                '',
                'echo "# BEGIN SECTION: Run Dockerfile - build and test"',
                'ls -al $WORKSPACE/ros_buildfarm/scripts/command',
                'docker.io run' +
                ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm' +
                ' -v $WORKSPACE/catkin_workspace:/tmp/catkin_workspace' +
                ' build_and_test',
                'echo "# END SECTION"',
            ]),
        }),
        '-PUBLISHERS': expand_template(
            'snippet/publisher_junit.xml.em', {
                'test_results': 'catkin_workspace/build_isolated/**/*.xml',
            }
        ) + expand_template(
            'snippet/publisher_mailer.xml.em', {
                'recipients': build_file.notify_emails,
                'send_to_individuals': True,
            }
        ),
        '-BUILD_WRAPPERS': expand_template(
            'snippet/build-wrapper_build-timeout.xml.em', {
                'timeout_minutes': 120,
            }
        ),
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
