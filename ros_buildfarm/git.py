import os
import subprocess


def get_ros_buildfarm_url():
    # NOTE __file__ refers to filepath of the
    # current module (i.e. the path of git.py).
    return get_repository_url(os.path.dirname(__file__))


def get_repository_url(path=None):
    url = subprocess.check_output(['git', 'config', 'remote.origin.url'])
    url = url.decode().rstrip()
    prefix_mapping = {
        'git@github.com:': 'https://github.com/',
    }
    for k, v in prefix_mapping.items():
        if url.startswith(k):
            url = v + url[len(k):]
    return url
