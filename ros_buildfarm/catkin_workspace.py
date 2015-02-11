import os
import shutil
import subprocess


def ensure_workspace_exists(workspace_root):
    # ensure that workspace exists
    assert os.path.exists(workspace_root), \
        "Workspace root '%s' does not exist" % workspace_root
    source_space = os.path.join(workspace_root, 'src')
    assert os.path.exists(source_space), \
        "Source space '%s' does not exist" % source_space


def clean_workspace(workspace_root):
    # clean up build, devel and install spaces
    build_space = os.path.join(workspace_root, 'build_isolated')
    if os.path.exists(build_space):
        shutil.rmtree(build_space)
    devel_space = os.path.join(workspace_root, 'devel_isolated')
    if os.path.exists(devel_space):
        shutil.rmtree(devel_space)
    install_space = os.path.join(workspace_root, 'install_isolated')
    if os.path.exists(install_space):
        shutil.rmtree(install_space)
    test_results_dir = os.path.join(workspace_root, 'test_results')
    if os.path.exists(test_results_dir):
        shutil.rmtree(test_results_dir)


def call_catkin_make_isolated(
        rosdistro_name, workspace_root, args, parent_result_space=None):
    # command to run
    script_name = 'catkin_make_isolated'
    # use script from source space if available
    source_space = os.path.join(workspace_root, 'src')
    script_from_source = os.path.join(
        source_space, 'catkin', 'bin', script_name)
    if os.path.exists(script_from_source):
        script_name = script_from_source
    cmd = ' '.join(
        ['PYTHONIOENCODING=utf_8', 'PYTHONUNBUFFERED=1', script_name] + args)

    # prepend setup file if available
    if not parent_result_space:
        parent_result_space = '/opt/ros/%s' % rosdistro_name
    setup_file = os.path.join(parent_result_space, 'setup.sh')
    if os.path.exists(setup_file):
        cmd = '. %s && %s' % (setup_file, cmd)

    print("Invoking '%s' in '%s'" % (cmd, workspace_root))
    return subprocess.call(cmd, cwd=workspace_root, shell=True)
