import os
import subprocess


def get_repository_url(path=None):
    if path is None:
        path = os.path.dirname(os.path.dirname(__file__))
    url = _get_git_remote_origin(path)
    assert url

    prefix_mapping = {
        'git@github.com:': 'https://github.com/',
    }
    for k, v in prefix_mapping.items():
        if url.startswith(k):
            url = v + url[len(k):]
    return url


def _get_git_remote_origin(path):
    git = _find_executable('git')
    if git:
        url = subprocess.check_output(
            [git, 'config', 'remote.origin.url'], cwd=path)
        return url.decode().rstrip()
    else:
        # find base path of the git working copy
        basepath = os.path.abspath(path)
        while True:
            if os.path.exists(os.path.join(basepath, '.git')):
                break
            parent_path = os.path.dirname(basepath)
            if parent_path == basepath:
                return None
            basepath = parent_path

        # extract url of remote origin from git config
        with open(os.path.join(basepath, '.git', 'config'), 'r') as h:
            lines = h.read().splitlines()
        section = '[remote "origin"]'
        if section not in lines:
            return None
        section_index = lines.index(section)

        index = section_index + 1
        while index < len(lines):
            line = lines[index]
            if line.startswith('['):
                return None
            line = line.lstrip()
            line_parts = line.split(' = ', 1)
            if line_parts[0] == 'url':
                return line_parts[1]
            index += 1
        return None


def _find_executable(file_name):
    for path in os.getenv('PATH').split(os.path.pathsep):
        file_path = os.path.join(path, file_name)
        if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
            return file_path
    return None
