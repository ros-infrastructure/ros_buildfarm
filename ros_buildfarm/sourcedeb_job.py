import subprocess

from catkin_pkg.package import parse_package
from rosdistro import get_distribution_file
from rosdistro import get_index


def add_argument_source_dir(parser):
    parser.add_argument(
        '--source-dir',
        required=True,
        help='The path to the package sources')


def get_sources(
        rosdistro_index_url, rosdistro_name, pkg_name, os_name, os_code_name,
        sources_dir):
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
    return 'debian/ros-%s-%s_%s_%s' % \
        (rosdistro_name, pkg_name.replace('_', '-'), pkg_version, os_code_name)


def build_sourcedeb(sources_dir):
    cmd = [
        'git', 'config',
        '--file', 'debian/gbp.conf',
        'git-buildpackage.upstream-branch']
    upstream_tag = subprocess.check_output(cmd, cwd=sources_dir)
    upstream_tag = upstream_tag.decode().rstrip()

    cmd = [
        'git', 'buildpackage',
        '--git-ignore-new',
        '--git-ignore-branch',
        # override wrong debian/gbp.conf values
        '--git-upstream-tag=' + upstream_tag,
        '--git-upstream-tree=tag',
        # dpkg-buildpackage args
        '-S', '-us', '-uc',
        # debuild args for lintian
        '--lintian-opts', '--suppress-tags', 'newer-standards-version']
    print("Invoking '%s' in '%s'" % (' '.join(cmd), sources_dir))
    subprocess.check_call(cmd, cwd=sources_dir)
