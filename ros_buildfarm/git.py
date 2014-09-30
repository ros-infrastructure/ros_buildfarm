import subprocess


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
