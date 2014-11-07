import os
import subprocess

from ros_buildfarm.common import get_debian_package_name


def get_sources(
        rosdistro_index_url, rosdistro_name, pkg_name, os_name, os_code_name,
        sources_dir):
    from rosdistro import get_distribution_file
    from rosdistro import get_index
    index = get_index(rosdistro_index_url)
    dist_file = get_distribution_file(index, rosdistro_name)
    if pkg_name not in dist_file.release_packages:
        return "Not a released package name: %s" % pkg_name

    pkg = dist_file.release_packages[pkg_name]
    repo_name = pkg.repository_name
    repo = dist_file.repositories[repo_name]
    if not repo.release_repository.version:
        return "Repository '%s' has no release version" % repo_name

    pkg_version = repo.release_repository.version
    print("Package '%s' version: %s" % (pkg_name, pkg_version))

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


def upload_sourcedeb(
        rosdistro_name, package_name, os_code_name, sourcedeb_dir,
        upload_host):
    # ensure that one deb file exists
    debian_package_name = get_debian_package_name(rosdistro_name, package_name)
    source_changes_files = _get_source_changes_files(
        sourcedeb_dir, debian_package_name)
    assert len(source_changes_files) == 1
    source_changes_file = source_changes_files[0]

    debian_tar_gz_file = source_changes_file[:-15] + '.debian.tar.gz'
    dsc_file = source_changes_file[:-15] + '.dsc'
    index = source_changes_file.find(
        '-',
        len(os.path.dirname(source_changes_file)) + len(debian_package_name))
    orig_tar_gz_file = source_changes_file[:index] + '.orig.tar.gz'

    # upload related files
    files = [
        source_changes_file, debian_tar_gz_file, dsc_file, orig_tar_gz_file]
    for f in files:
        assert os.path.exists(f)

    cmd = [
        '/usr/bin/scp',
        '-o', 'StrictHostKeyChecking=no',
    ]
    cmd += files
    # TODO upload to build specific subfolder
    cmd.append(
        'jenkins-slave@%s:/var/repos/ubuntu/building/queue/%s/' %
        (upload_host, os_code_name))
    print("Invoking '%s'" % ' '.join(cmd))
    subprocess.check_call(cmd)


def _get_source_changes_files(basepath, debian_package_name):
    files = []
    for filename in os.listdir(basepath):
        if not filename.startswith('%s_' % debian_package_name):
            continue
        if not filename.endswith('_source.changes'):
            continue
        path = os.path.join(basepath, filename)
        files.append(path)
    return files
