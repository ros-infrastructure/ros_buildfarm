#import os
#import shutil
import subprocess

#from catkin_pkg.package import parse_package

from ros_buildfarm.common import get_debian_package_name


def get_sourcedeb(rosdistro_name, package_name, sourcedeb_dir):
    debian_package_name = get_debian_package_name(rosdistro_name, package_name)

    # TODO
    # index = package_version.find('-')
    # assert index != -1
    # version_without_debinc = package_version[index]
    # source_dir = os.path.join(
    #     sourcedeb_dir, '%s-%s' % (debian_package_name, version_without_debinc))

    # if os.path.exists(source_dir):
    #     shutil.rmtree(source_dir)

    cmd = ['apt-get', 'source', debian_package_name]
    print("Invoking '%s'" % ' '.join(cmd))
    subprocess.check_call(cmd, cwd=sourcedeb_dir)

    # index = package_version.find('-')
    # assert index != -1
    # version_without_debinc = package_version[index]
    # source_dir = os.path.join(
    #     sourcedeb_dir, '%s-%s' % (debian_package_name, version_without_debinc))

    # assert os.path.exists(source_dir)

    # print("Package '%s' version: %s" % (debian_package_name, package_version))

    # pkg = parse_package(source_dir)
    # maintainer_emails = set([])
    # for m in pkg.maintainers:
    #     maintainer_emails.add(m.email)
    # if maintainer_emails:
    #     print('Package maintainer emails: %s' %
    #           ' '.join(sorted(maintainer_emails)))


def build_binarydeb(source_dir):
    # get package name and version from changelog
    cmd = ['dpkg-parsechangelog']
    output = subprocess.check_output(cmd, cwd=source_dir)
    pkg_name = None
    pkg_version = None
    for line in output.decode().splitlines():
        if line.startswith('Source: '):
            pkg_name = line[8:]
        if line.startswith('Version: '):
            pkg_version = line[9:]
    assert pkg_name is not None
    assert pkg_version is not None

    cmd = ['apt-src', 'import', pkg_name, '--here', '--version', pkg_version]
    subprocess.check_call(cmd, cwd=source_dir)

    cmd = ['apt-src', 'build', pkg_name]
    print("Invoking '%s' in '%s'" % (' '.join(cmd), source_dir))
    subprocess.check_call(cmd, cwd=source_dir)
