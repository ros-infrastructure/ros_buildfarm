import os

from setuptools import find_packages
from setuptools import setup

# Get a list of scripts to install
scripts = []
for root, dirnames, filenames in os.walk('scripts'):
    # don't install the wrapper scripts
    # since they would overlay Python packages with the same name
    if 'wrapper' in dirnames:
        dirnames.remove('wrapper')
    for filename in filenames:
        if not filename.endswith('.py'):
            continue
        scripts.append(os.path.join(root, filename))

# Get the long description out of the readme.md
with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r') as f:
    long_description = f.read()

kwargs = {
    'name': 'ros_buildfarm',
    # same version as in:
    # - ros_buildfarm/__init__.py
    # - stdeb.cfg
    'version': '3.0.1-master',
    'packages': find_packages(exclude=['test']),
    'package_data': {
        'ros_buildfarm.templates': [
            '*/*/*.css',
            '*.em',
            '*/*.em',
            '*/*/*.em',
            '*/*.groovy',
            '*/*/*.js',
            '*/*/*.parser',
        ],
    },
    'scripts': scripts,
    'zip_safe': False,
    'install_requires': [
        'empy<4',
        'PyYAML'],
    'extras_require': {
        'test': [
            'flake8 >= 3.7, < 5',
            'flake8-class-newline',
            'flake8_docstrings',
            'flake8-import-order',
            'pep8',
            'pycodestyle < 2.9.0',
            'pyflakes < 2.5.0',
            'pytest'],
    },
    'author': 'Dirk Thomas',
    'author_email': 'dthomas@osrfoundation.org',
    'maintainer': 'ROS Infrastructure Team',
    'project_urls': {
        'Source code':
        'https://github.com/ros-infrastructure/ros_buildfarm',
        'Issue tracker':
        'https://github.com/ros-infrastructure/ros_buildfarm/issues',
    },
    'url': 'https://github.com/ros-infrastructure/ros_buildfarm',
    'keywords': ['ROS', 'buildfarm', 'catkin'],
    'classifiers': [
        'Programming Language :: Python',
        'License :: OSI Approved :: Apache Software License'],
    'description': "Build farm used to build the ROS ecosystem's packages.",
    'long_description': long_description,
    'license': 'Apache 2.0',
}

if os.sys.version_info[0] == 2:
    kwargs['install_requires'].append('configparser')

if 'SKIP_PYTHON_MODULES' in os.environ:
    kwargs['packages'] = []
elif 'SKIP_PYTHON_SCRIPTS' in os.environ:
    kwargs['name'] += '_modules'
    kwargs['scripts'] = []
else:
    kwargs['install_requires'] += [
        'catkin_pkg >= 0.2.6', 'jenkinsapi', 'rosdistro >= 0.4.0', 'vcstool >= 0.1.37']

setup(**kwargs)
