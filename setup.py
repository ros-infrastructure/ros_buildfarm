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
    'version': '2.0.1',  # same version as in ros_buildfarm/__init__.py
    'packages': find_packages(exclude=['test']),
    'scripts': scripts,
    'include_package_data': True,
    'zip_safe': False,
    'install_requires': [
        'empy',
        'PyYAML'],
    'author': 'Dirk Thomas',
    'author_email': 'dthomas@osrfoundation.org',
    'maintainer': 'Dirk Thomas',
    'maintainer_email': 'dthomas@osrfoundation.org',
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
    kwargs['install_requires'] += ['catkin_pkg >= 0.2.6', 'rosdistro >= 0.4.0']

setup(**kwargs)
