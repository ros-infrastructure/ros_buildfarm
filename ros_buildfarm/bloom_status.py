import os
import re
import time
import yaml
import requests
import shutil
from .templates import expand_template, get_template_path
from github import Github, GithubException

TOKEN_PATTERN = re.compile('https://([^@]*)@?github.com/.*git')
ORG_PATTERN = re.compile('https://.*github.com/([^/]+)/.*git')


def _download_yaml(url):
    r = requests.get(url)
    return yaml.load(r.text)


def _get_distro_info(distros=None):
    info = {}
    main_url = os.environ['ROSDISTRO_INDEX_URL']
    folder = os.path.split(main_url)[0]
    D = _download_yaml(main_url)
    for distro_name, distro_info in D['distributions'].items():
        if distros is not None and distro_name not in distros:
            continue
        url_part = distro_info['distribution'][0]
        new_url = os.path.join(folder, url_part)
        info[distro_name] = _download_yaml(new_url)
    if distros is not None:
        remaining = set(distros) - set(info.keys())
        for distro in remaining:
            print('Warning! Distro "{}" not found.'.format(distro))
    return info


def _extract_token(distro_info):
    for distro, distro_data in distro_info.items():
        for name, d in distro_data['repositories'].items():
            if 'source' not in d:
                continue
            m = TOKEN_PATTERN.match(d['source'].get('url', ''))
            if m:
                if len(m.group(1)):
                    return m.group(1)


def _get_package_info(distro_info):
    packages = {}
    for distro, distro_data in distro_info.items():
        for name, d in distro_data['repositories'].items():
            if name not in packages:
                pkg = {}
                packages[name] = pkg
            else:
                pkg = packages[name]
            pkg[distro] = {}

            if 'source' in d:
                upstream = d['source'].get('version', None)
                if upstream:
                    pkg[distro]['upstream'] = upstream
                m = ORG_PATTERN.match(d['source'].get('url', ''))
                if m:
                    pkg[distro]['org'] = m.group(1)

            release = d.get('release', {}).get('version', None)
            if release:
                if '-' in release:
                    release = release.partition('-')[0]
                pkg[distro]['release'] = release
    return packages


def _get_package_status(g, name, branch_info):
    if 'upstream' not in branch_info or 'org' not in branch_info:
        return 'NO SOURCE'
    elif 'release' not in branch_info:
        return 'NO RELEASE'
    try:
        repo = g.get_repo(branch_info['org'] + '/' + name)
        the_diff = repo.compare(branch_info['release'], branch_info['upstream'])
        if len(the_diff.commits) > 0:
            return 'CHANGED'
        else:
            return 'BLOOMED'
    except GithubException as e:
        print(e)
        return 'BROKEN'


def _query_package_statuses(g, package_info):
    for pkg_name, info in package_info.items():
        for distro, d_info in info.items():
            status = _get_package_status(g, pkg_name, d_info)
            d_info['status'] = status


def build_bloom_status_page(distros=None, output_dir='.'):
    start_time = time.time()
    distro_info = _get_distro_info(distros)
    token = _extract_token(distro_info)
    package_info = _get_package_info(distro_info)
    if token:
        g = Github(token)
    else:
        g = Github()
    _query_package_statuses(g, package_info)

    data = {
        'start_time': start_time,
        'start_time_local_str': time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime(start_time)),
        'packages': package_info,
        'distros': list(distro_info.keys())
    }

    template_name = 'status/bloom_status_page.html.em'
    html = expand_template(template_name, data)
    output_filename = os.path.join(output_dir, 'bloom_status.html')
    print("Generating bloom status page '%s':" % output_filename)
    with open(output_filename, 'w') as h:
        h.write(html)
    for subfolder in ['css', 'js']:
        dst = os.path.join(output_dir, subfolder)
        if not os.path.exists(dst):
            src = get_template_path(os.path.join('status', subfolder))
            shutil.copytree(src, dst)
