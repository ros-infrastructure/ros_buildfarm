import configparser
import os
import subprocess


def get_ros_buildfarm_url():
    # NOTE __file__ refers to filepath of the
    # current module (i.e. the path of git.py).
    return get_repository_url(os.path.dirname(__file__))


def get_repository_url(path=None):
    url = _try_get_repository_url(path)
    url = url.rstrip()
    prefix_mapping = {
        'git@github.com:': 'https://github.com/',
    }
    for k, v in prefix_mapping.items():
        if url.startswith(k):
            url = v + url[len(k):]
    return url


def _try_get_repository_url(path):
    # Try using native git
    url = _get_repository_url_with_native_git(path)
    if url is not None:
        return url
    # Try using emulation
    print('Falling back to directly reading the git '
          'config file to obtain the repository url.')
    url = _get_repository_url_with_emulation(path)
    # Check success
    assert url is not None, "get_repository_url() failed for path %s" % path
    return url


def _get_repository_url_with_native_git(path):
    try:
        return subprocess.check_output(['git', 'config', 'remote.origin.url'], universal_newlines=True)
    except FileNotFoundError as error:
        print("Native git executable is not available (%s)." % error)
        return None


def _get_repository_url_with_emulation(path):
    """
    Alternative for _get_repository_url_with_native_git when git is not available (e.g. inside Docker).
    """
    git_root = _find_git_root(path)
    repo_url = _read_git_config(git_root, 'remote "origin"', "url") if git_root is not None else None
    return repo_url


def _find_git_root(path=None):
    path = os.getcwd() if path is None else path
    path = os.path.abspath(path)
    for parent_dir in _walkup(path):
        git_dir = os.path.join(parent_dir, '.git')
        if os.path.exists(git_dir):
            return git_dir
    return None


def _walkup(path):
    at_top = False
    while not at_top:
        yield path
        parent_path = os.path.dirname(path)
        if parent_path == path:
            at_top = True
        else:
            path = parent_path


def _read_git_config(git_root, section, key):
    config = configparser.ConfigParser()
    config.read(os.path.join(git_root, 'config'))
    return config[section][key]
