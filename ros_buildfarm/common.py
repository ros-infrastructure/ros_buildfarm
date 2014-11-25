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


def get_repositories_and_script_generating_key_files(config, build_file):
    # extract the distribution repository urls and keys from the build file
    # and pass them as command line arguments and files
    # so that the job must not parse the build file
    repository_urls = []
    repository_keys = []
    if 'debian_repositories' in config.prerequisites:
        repository_urls += config.prerequisites['debian_repositories']
    if 'debian_repository_keys' in config.prerequisites:
        repository_keys += config.prerequisites['debian_repository_keys']
    assert len(repository_urls) == len(repository_keys)

    assert len(build_file.repository_urls) == len(build_file.repository_keys)
    repository_urls += build_file.repository_urls
    repository_keys += build_file.repository_keys

    # remove duplicate urls
    unique_repository_urls = []
    unique_repository_keys = []
    for i, url in enumerate(repository_urls):
        if url not in unique_repository_urls:
            unique_repository_urls.append(url)
            unique_repository_keys.append(repository_keys[i])

    repository_args = []
    if unique_repository_urls:
        repository_args.append('--distribution-repository-urls')
        repository_args += unique_repository_urls

    script_generating_key_files = []
    if unique_repository_keys:
        repository_args.append('--distribution-repository-key-files')
        script_generating_key_files.append("mkdir -p $WORKSPACE/keys")
        script_generating_key_files.append("rm -fr $WORKSPACE/keys/*")
        for i, repository_key in enumerate(unique_repository_keys):
            repository_args.append('$WORKSPACE/keys/%d.key' % i)
            script_generating_key_files.append(
                'echo "%s" > $WORKSPACE/keys/%d.key' % (repository_key, i))

    return repository_args, script_generating_key_files


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
