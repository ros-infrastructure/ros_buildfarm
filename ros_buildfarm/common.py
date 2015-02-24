from collections import namedtuple
import os


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


Target = namedtuple('Target', 'os_name os_code_name arch')


def get_repositories_and_script_generating_key_files(
        config=None, build_file=None):
    # extract the distribution repository urls and keys from the build file
    # and pass them as command line arguments and files
    # so that the job must not parse the build file
    repository_urls = []
    repository_keys = []
    if config:
        if 'debian_repositories' in config.prerequisites:
            repository_urls += config.prerequisites['debian_repositories']
        if 'debian_repository_keys' in config.prerequisites:
            repository_keys += config.prerequisites['debian_repository_keys']
        assert len(repository_urls) == len(repository_keys)

    if build_file:
        assert len(build_file.repository_urls) == \
            len(build_file.repository_keys)
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


def get_debian_package_name_prefix(rosdistro_name):
    return 'ros-%s-' % rosdistro_name


def get_debian_package_name(rosdistro_name, ros_package_name):
    return '%s%s' % \
        (get_debian_package_name_prefix(rosdistro_name),
         ros_package_name.replace('_', '-'))


def get_devel_view_name(rosdistro_name, source_build_name, pull_request=False):
    name = '%s%s' % (
        rosdistro_name[0].upper(),
        'dev' if not pull_request else 'pr')
    short_source_build_name = get_short_build_name(source_build_name)
    if short_source_build_name:
        name += '_%s' % short_source_build_name
    return name


def get_devel_job_name(rosdistro_name, source_build_name,
                       repo_name, os_name, os_code_name, arch,
                       pull_request=False):
    view_name = get_devel_view_name(
        rosdistro_name, source_build_name, pull_request=pull_request)
    job_name = '%s__%s__%s_%s_%s' % \
        (view_name, repo_name, os_name, os_code_name, arch)
    return job_name


def get_doc_view_name(rosdistro_name, doc_build_name):
    name = '%sdoc' % rosdistro_name[0].upper()
    short_doc_build_name = get_short_build_name(doc_build_name)
    if short_doc_build_name:
        name += '_%s' % short_doc_build_name
    return name


def get_release_job_prefix(rosdistro_name, release_build_name=None):
    prefix = '%srel' % rosdistro_name[0].upper()
    if release_build_name is not None:
        short_release_build_name = get_short_build_name(release_build_name)
        if short_release_build_name:
            prefix += '_%s' % short_release_build_name
    return prefix


def get_release_view_name(
        rosdistro_name, release_build_name, os_name, os_code_name, arch):
    if arch == 'source':
        return get_release_source_view_name(
            rosdistro_name, os_name, os_code_name)
    else:
        return get_release_binary_view_name(
            rosdistro_name, release_build_name, os_name, os_code_name, arch)


def get_release_source_view_prefix(rosdistro_name):
    return '%s%s' % (rosdistro_name[0].upper(), 'src')


def get_release_source_view_name(
        rosdistro_name, os_name, os_code_name):
    return '%s_%s%s' % (
        get_release_source_view_prefix(rosdistro_name),
        get_short_os_name(os_name),
        get_short_os_code_name(os_code_name))


def get_sourcedeb_job_name(rosdistro_name, release_build_name,
                           pkg_name, os_name, os_code_name):
    view_name = get_release_source_view_name(
        rosdistro_name, os_name, os_code_name)
    return '%s__%s__%s_%s__source' % \
        (view_name, pkg_name, os_name, os_code_name)


def get_release_binary_view_prefix(rosdistro_name, release_build_name):
    prefix = '%s%s' % (rosdistro_name[0].upper(), 'bin')
    short_release_build_name = get_short_build_name(release_build_name)
    if short_release_build_name:
        prefix += '_%s' % short_release_build_name
    return prefix


def get_release_binary_view_name(
        rosdistro_name, release_build_name, os_name, os_code_name, arch):
    os_code_name = get_short_os_code_name(os_code_name)
    arch = get_short_arch(arch)
    return '%s_%s%s%s' % (
        get_release_binary_view_prefix(rosdistro_name, release_build_name),
        get_short_os_name(os_name),
        get_short_os_code_name(os_code_name),
        get_short_arch(arch))


def get_binarydeb_job_name(rosdistro_name, release_build_name,
                           pkg_name, os_name, os_code_name, arch):
    view_name = get_release_binary_view_name(
        rosdistro_name, release_build_name, os_name, os_code_name, arch)
    return '%s__%s__%s_%s_%s__binary' % \
        (view_name, pkg_name, os_name, os_code_name, arch)


def get_short_build_name(build_name):
    build_name_mappings = {
        'default': '',
    }
    return build_name_mappings.get(build_name, build_name)


def get_short_os_name(os_name):
    os_name_mappings = {
        'ubuntu': 'u',
    }
    return os_name_mappings.get(os_name, os_name)


def get_short_os_code_name(os_code_name):
    os_code_name_mappings = {
        'saucy': 'S',
        'trusty': 'T',
        'utopic': 'U',
        'vivid': 'V',
    }
    return os_code_name_mappings.get(os_code_name, os_code_name)


def get_short_arch(arch):
    arch_mappings = {
        'amd64': '64',
        'armhf': 'hf',
        'i386': '32',
    }
    return arch_mappings.get(arch, arch)


def git_github_orgunit(url):
    prefix = 'https://github.com/'
    if not url.startswith(prefix):
        return None
    path = url[len(prefix):]
    index = path.index('/')
    return path[:index]


def get_github_project_url(url):
    if not url.startswith('https://github.com/'):
        return None
    git_suffix = '.git'
    if not url.endswith(git_suffix):
        return None
    url = url[:-len(git_suffix)] + '/'
    return url


def get_user_id():
    uid = os.getuid()
    assert uid != 0, "You can not run this as user 'root'"
    return uid


def find_executable(file_name):
    for path in os.getenv('PATH').split(os.path.pathsep):
        file_path = os.path.join(path, file_name)
        if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
            return file_path
    return None


def get_doc_job_name(rosdistro_name, doc_build_name,
                     repo_name, os_name, os_code_name, arch):
    view_name = get_doc_view_name(
        rosdistro_name, doc_build_name)
    job_name = '%s__%s__%s_%s_%s' % \
        (view_name, repo_name, os_name, os_code_name, arch)
    return job_name


def get_doc_job_url(
        jenkins_url, rosdistro_name, doc_build_name, repository_name, os_name,
        os_code_name, arch):
    return _get_job_url(
        jenkins_url,
        get_doc_view_name(rosdistro_name, doc_build_name),
        get_doc_job_name(
            rosdistro_name, doc_build_name, repository_name, os_name,
            os_code_name, arch)
    )


def get_devel_job_urls(
        jenkins_url, source_build_files, rosdistro_name, repository_name):
    urls = set([])
    for source_build_name in source_build_files.keys():
        build_file = source_build_files[source_build_name]
        for os_name in build_file.targets.keys():
            for os_code_name in build_file.targets[os_name].keys():
                for arch in build_file.targets[os_name][os_code_name]:
                    job_url = _get_job_url(
                        jenkins_url,
                        get_devel_view_name(rosdistro_name, source_build_name),
                        get_devel_job_name(
                            rosdistro_name, source_build_name, repository_name,
                            os_name, os_code_name, arch)
                    )
                    urls.add(job_url)
    return urls


def get_release_job_urls(
        jenkins_url, release_build_files, rosdistro_name, package_name):
    urls = set([])
    for release_build_name in release_build_files.keys():
        build_file = release_build_files[release_build_name]
        for os_name in build_file.targets.keys():
            for os_code_name in build_file.targets[os_name].keys():
                job_url = _get_job_url(
                    jenkins_url,
                    get_release_source_view_name(
                        rosdistro_name, os_name, os_code_name),
                    get_sourcedeb_job_name(
                        rosdistro_name, release_build_name,
                        package_name, os_name, os_code_name)
                )
                urls.add(job_url)

                for arch in build_file.targets[os_name][os_code_name]:
                    job_url = _get_job_url(
                        jenkins_url,
                        get_release_binary_view_name(
                            rosdistro_name, release_build_name,
                            os_name, os_code_name, arch),
                        get_binarydeb_job_name(
                            rosdistro_name, release_build_name,
                            package_name, os_name, os_code_name, arch)
                    )
                    urls.add(job_url)
    return urls


def _get_job_url(jenkins_url, view_name, job_name):
    return '%s/view/%s/job/%s' % (jenkins_url, view_name, job_name)
