import os
import subprocess
import sys

from setuptools import find_packages
from setuptools import setup

install_requires = [
    'catkin-pkg >= 0.2.6',
    'empy',
    'PyYAML',
    'rosdistro >= 0.4.0',
]

# Get the long description out of the readme.md
this_dir = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_dir, 'README.md'), 'r') as f:
    long_description = f.read()

# Get a list of scripts to install
scripts = []
for root, dirnames, filenames in os.walk('scripts'):
    for filename in filenames:
        scripts.append(os.path.join(root, filename))

# Attempt to get the default url based on current git environement
git_module_path = os.path.join(this_dir, 'ros_buildfarm', 'git.py')
output = subprocess.check_output([sys.executable, git_module_path])
with open(os.path.join(this_dir, 'ros_buildfarm', 'defaults.py'), 'w') as f:
    f.write(output.decode("utf-8"))

setup(
    name='ros_buildfarm',
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    scripts=scripts,
    include_package_data=True,
    install_requires=install_requires,
    author='Dirk Thomas, Tully Foote',
    author_email='dthomas@osrfoundation.org, tfoote@osrfoundation.org',
    maintainer='Dirk Thomas',
    maintainer_email='dthomas@osrfoundation.org',
    url='http://wiki.ros.org/ros_buildfarm',
    keywords=['ROS', 'buildfarm', 'catkin'],
    classifiers=['Programming Language :: Python',
                 'License :: OSI Approved :: Apache Software License'],
    description="Build farm used to build the ROS ecosystem's packages.",
    long_description=long_description,
    license='Apache 2.0',
)
