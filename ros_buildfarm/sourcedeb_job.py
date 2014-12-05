import subprocess

from ros_buildfarm.common import get_debian_package_name
from ros_buildfarm.release_common import dpkg_parsechangelog


def get_sources(
        rosdistro_index_url, rosdistro_name, pkg_name, os_name, os_code_name,
        sources_dir):
    from rosdistro import get_distribution_file
    from rosdistro import get_index
    index = get_index(rosdistro_index_url)
    dist_file = get_distribution_file(index, rosdistro_name)
    if pkg_name not in dist_file.release_packages:
        return 'Not a released package name: %s' % pkg_name

    pkg = dist_file.release_packages[pkg_name]
    repo_name = pkg.repository_name
    repo = dist_file.repositories[repo_name]
    if not repo.release_repository.version:
        return "Repository '%s' has no release version" % repo_name

    pkg_version = repo.release_repository.version
    tag = _get_source_tag(
        rosdistro_name, pkg_name, pkg_version, os_name, os_code_name)

    cmd = [
        'git', 'clone',
        '--branch', tag,
        # fetch all branches and tags but no history
        '--depth', '1', '--no-single-branch',
        repo.release_repository.url, sources_dir]

    print("Invoking '%s'" % ' '.join(cmd))
    subprocess.check_call(cmd)

    # ensure that the package version is correct
    source_version = dpkg_parsechangelog(sources_dir, ['Version'])[0]
    if not source_version.startswith(pkg_version) or \
            (len(source_version) > len(pkg_version) and
             source_version[len(pkg_version)] in '0123456789'):
        raise RuntimeError(
            ('The cloned package version from the GBP (%s) does not match ' +
             'the expected package version from the distribution file (%s)') %
            (source_version, pkg_version))

    # output package version for job description
    print("Package '%s' version: %s" % (pkg_name, source_version))

    # output package maintainers for job notification
    from catkin_pkg.package import parse_package
    pkg = parse_package(sources_dir)
    maintainer_emails = set([])
    for m in pkg.maintainers:
        maintainer_emails.add(m.email)
    if maintainer_emails:
        print('Package maintainer emails: %s' %
              ' '.join(sorted(maintainer_emails)))


def _get_source_tag(
        rosdistro_name, pkg_name, pkg_version, os_name, os_code_name):
    assert os_name == 'ubuntu'
    return 'debian/%s_%s_%s' % \
        (get_debian_package_name(rosdistro_name, pkg_name),
         pkg_version, os_code_name)


def build_sourcedeb(sources_dir):
    cmd = [
        'git', 'buildpackage',
        '--git-ignore-new',
        '--git-ignore-branch',
        # dpkg-buildpackage args
        '-S', '-us', '-uc',
        # debuild args for lintian
        '--lintian-opts', '--suppress-tags', 'newer-standards-version']

    # workaround for old gbp.conf values
    # https://github.com/ros-infrastructure/bloom/issues/211
    config_cmd = [
        'git', 'config',
        '--file', 'debian/gbp.conf',
        'git-buildpackage.upstream-tree']
    upstream_tree = subprocess.check_output(config_cmd, cwd=sources_dir)
    upstream_tree = upstream_tree.decode().rstrip()
    if upstream_tree != 'tag':
        config_cmd = [
            'git', 'config',
            '--file', 'debian/gbp.conf',
            'git-buildpackage.upstream-branch']
        upstream_tag = subprocess.check_output(config_cmd, cwd=sources_dir)
        upstream_tag = upstream_tag.decode().rstrip()
        cmd += [
            '--git-upstream-tag=' + upstream_tag,
            '--git-upstream-tree=tag']

    print("Invoking '%s' in '%s'" % (' '.join(cmd), sources_dir))
    subprocess.check_call(cmd, cwd=sources_dir)
