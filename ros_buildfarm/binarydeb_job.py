import os
import subprocess
from time import strftime

from ros_buildfarm.common import get_debian_package_name


def get_sourcedeb(rosdistro_name, package_name, sourcedeb_dir):
    # ensure that no source subfolder exists
    debian_package_name = get_debian_package_name(rosdistro_name, package_name)
    subfolders = _get_package_subfolders(sourcedeb_dir, debian_package_name)
    assert not subfolders, "Sourcedeb directory '%s' must not have any " + \
        "subfolders starting with '%s-'" % (sourcedeb_dir, package_name)

    debian_package_name = get_debian_package_name(rosdistro_name, package_name)
    cmd = ['apt-get', 'source', debian_package_name]
    print("Invoking '%s'" % ' '.join(cmd))
    subprocess.check_call(cmd, cwd=sourcedeb_dir)

    # ensure that one source subfolder exists
    subfolders = _get_package_subfolders(sourcedeb_dir, debian_package_name)
    assert len(subfolders) == 1
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
    assert len(subfolders) == 1
    source_dir = subfolders[0]

    source, version, distribution, urgency = _dpkg_parsechangelog(
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
    assert len(subfolders) == 1
    source_dir = subfolders[0]

    source, version = _dpkg_parsechangelog(
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


def _dpkg_parsechangelog(source_dir, fields):
    cmd = ['dpkg-parsechangelog']
    output = subprocess.check_output(cmd, cwd=source_dir)
    values = {}
    for line in output.decode().splitlines():
        for field in fields:
            prefix = '%s: ' % field
            if line.startswith(prefix):
                values[field] = line[len(prefix):]
    assert len(fields) == len(values.keys())
    return [values[field] for field in fields]


def upload_binarydeb(
        rosdistro_name, package_name, os_code_name, sourcedeb_dir,
        upload_host):
    # ensure that one deb file exists
    debian_package_name = get_debian_package_name(rosdistro_name, package_name)
    deb_files = _get_deb_files(sourcedeb_dir, debian_package_name)
    assert len(deb_files) == 1
    deb_file = deb_files[0]

    changes_file = deb_file[:-3] + 'changes'

    # upload related files
    files = [deb_file, changes_file]
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


def _get_deb_files(basepath, debian_package_name):
    files = []
    for filename in os.listdir(basepath):
        if not filename.startswith('%s_' % debian_package_name):
            continue
        if not filename.endswith('.deb'):
            continue
        path = os.path.join(basepath, filename)
        files.append(path)
    return files
