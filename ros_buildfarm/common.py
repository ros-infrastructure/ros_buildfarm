from collections import namedtuple


class OSTarget(namedtuple('OSTarget', 'os_name os_code_name')):
    """
    Specifies the target OS of a build.

    The target OS is given as a combination of OS name and OS code name.
    """

    def __str__(self):
        return '%s %s' % (self.os_name, self.os_code_name)


class JobValidationError(Exception):
    """
    Indicates that the validation of a build job failed.

    This exception is raised by the reconfigure_*_job functions
    if validation fails, e.g. because the requested package
    is not available in the specified index.yaml
    """

    def __init__(self, message):
        self.message = message


class Scope(object):

    def __init__(self, scope_name, description):
        self.scope_name = scope_name
        self.description = description

    def __enter__(self):
        print('# BEGIN %s: %s' % (self.scope_name, self.description))

    def __exit__(self, type, value, traceback):
        print('# END %s' % self.scope_name)


def get_apt_mirrors_and_script_generating_key_files(conf):
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
    return apt_mirror_args, script_generating_key_files


def get_distribution_repository_keys(urls, key_files):
    # ensure that for each key file a url has been passed
    assert \
        len(urls) >= \
        len(key_files), \
        'More distribution repository keys (%d) passes in then urls (%d)' % \
        (len(key_files),
         len(urls))

    distribution_repositories = []
    for i, url in enumerate(urls):
        key_file = key_files[i] \
            if len(key_files) > i \
            else ''
        distribution_repositories.append((url, key_file))
    print('Using the following distribution repositories:')
    keys = []
    for url, key_file in distribution_repositories:
        print('  %s%s' % (url, ' (%s)' % key_file if key_file else ''))
        with open(key_file, 'r') as h:
            keys.append(h.read())
    return keys


def get_binary_package_versions(apt_cache, debian_pkg_names):
    versions = {}
    for debian_pkg_name in debian_pkg_names:
        pkg = apt_cache[debian_pkg_name]
        versions[debian_pkg_name] = max(pkg.versions).version
    return versions


def get_debian_package_name(rosdistro_name, ros_package_name):
    return 'ros-%s-%s' % (rosdistro_name, ros_package_name.replace('_', '-'))


def get_devel_view_name(rosdistro_name, source_build_name):
    return '%sdev%s' % (rosdistro_name[0].upper(), source_build_name)


def get_release_view_name(rosdistro_name, release_build_name):
    return '%srel%s' % (rosdistro_name[0].upper(), release_build_name)
