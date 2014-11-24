import os
import subprocess
from time import strftime

from ros_buildfarm.common import get_debian_package_name
from ros_buildfarm.release_common import dpkg_parsechangelog


def get_sourcedeb(
        rosdistro_name, package_name, sourcedeb_dir,
        skip_download_sourcedeb=False):
    # ensure that no source subfolder exists
    debian_package_name = get_debian_package_name(rosdistro_name, package_name)
    subfolders = _get_package_subfolders(sourcedeb_dir, debian_package_name)
    assert not subfolders, \
        ("Sourcedeb directory '%s' must not have any " +
         "subfolders starting with '%s-'") % (sourcedeb_dir, package_name)

    debian_package_name = get_debian_package_name(rosdistro_name, package_name)
    if not skip_download_sourcedeb:
        # download sourcedeb
        cmd = ['apt-get', 'source', debian_package_name, '--download-only']
        print("Invoking '%s'" % ' '.join(cmd))
        subprocess.check_call(cmd, cwd=sourcedeb_dir)

    # extract sourcedeb
    filenames = _get_package_dsc_filename(sourcedeb_dir, debian_package_name)
    assert len(filenames) == 1, filenames
    dsc_filename = filenames[0]
    cmd = ['dpkg-source', '-x', dsc_filename]
    print("Invoking '%s'" % ' '.join(cmd))
    subprocess.check_call(cmd, cwd=sourcedeb_dir)

    # ensure that one source subfolder exists
    subfolders = _get_package_subfolders(sourcedeb_dir, debian_package_name)
    assert len(subfolders) == 1, subfolders
    source_dir = subfolders[0]

    # output package maintainers for job notification
    from catkin_pkg.package import parse_package
    pkg = parse_package(source_dir)
    maintainer_emails = set([])
    for m in pkg.maintainers:
        maintainer_emails.add(m.email)
    if maintainer_emails:
        print('Package maintainer emails: %s' %
              ' '.join(sorted(maintainer_emails)))


def append_build_timestamp(rosdistro_name, package_name, sourcedeb_dir):
    # ensure that one source subfolder exists
    debian_package_name = get_debian_package_name(rosdistro_name, package_name)
    subfolders = _get_package_subfolders(sourcedeb_dir, debian_package_name)
    assert len(subfolders) == 1, subfolders
    source_dir = subfolders[0]

    source, version, distribution, urgency = dpkg_parsechangelog(
        source_dir, ['Source', 'Version', 'Distribution', 'Urgency'])
    cmd = [
        'debchange',
        '-v', '%s-%s' % (version, strftime('%Y%m%d-%H%M%S%z')),
        '-p',  # preserve directory name
        '-D', distribution,
        '-u', urgency,
        '-m',  # keep maintainer details
        'Append timestamp when binarydeb was built.',
    ]
    print("Invoking '%s' in '%s'" % (' '.join(cmd), source_dir))
    subprocess.check_call(cmd, cwd=source_dir)


def build_binarydeb(rosdistro_name, package_name, sourcedeb_dir):
    # ensure that one source subfolder exists
    debian_package_name = get_debian_package_name(rosdistro_name, package_name)
    subfolders = _get_package_subfolders(sourcedeb_dir, debian_package_name)
    assert len(subfolders) == 1, subfolders
    source_dir = subfolders[0]

    source, version = dpkg_parsechangelog(
        source_dir, ['Source', 'Version'])
    # output package version for job description
    print("Package '%s' version: %s" % (debian_package_name, version))

    cmd = ['apt-src', 'import', source, '--here', '--version', version]
    subprocess.check_call(cmd, cwd=source_dir)

    cmd = ['apt-src', 'build', source]
    print("Invoking '%s' in '%s'" % (' '.join(cmd), source_dir))
    subprocess.check_call(cmd, cwd=source_dir)


def _get_package_subfolders(basepath, debian_package_name):
    subfolders = []
    for filename in os.listdir(basepath):
        path = os.path.join(basepath, filename)
        if not os.path.isdir(path):
            continue
        if filename.startswith('%s-' % debian_package_name):
            subfolders.append(path)
    return subfolders


def _get_package_dsc_filename(basepath, debian_package_name):
    filenames = []
    for filename in os.listdir(basepath):
        if filename.startswith('%s_' % debian_package_name) and \
                filename.endswith('.dsc'):
            filenames.append(filename)
    return filenames
