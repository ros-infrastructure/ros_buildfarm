import os

from setuptools import find_packages
from setuptools import setup

# get version number from module
version_file = os.path.join(
    os.path.dirname(__file__), 'ros_buildfarm', '_version.py')
with open(version_file) as h:
    exec(h.read())

# Get a list of scripts to install
scripts = []
for root, dirnames, filenames in os.walk('scripts'):
    for filename in filenames:
        scripts.append(os.path.join(root, filename))

install_requires = [
    'catkin-pkg >= 0.2.6',
    'empy',
    'PyYAML',
    'rosdistro >= 0.4.0',
]

# Get the long description out of the readme.md
with open(os.path.join(os.path.dirname(__file__), 'README.md'), 'r') as f:
    long_description = f.read()

setup(
    name='ros_buildfarm',
    version=__version__,
    packages=find_packages(exclude=['test']),
    scripts=scripts,
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    author='Dirk Thomas',
    author_email='dthomas@osrfoundation.org',
    maintainer='Dirk Thomas',
    maintainer_email='dthomas@osrfoundation.org',
    url='https://github.com/ros-infrastructure/ros_buildfarm',
    keywords=['ROS', 'buildfarm', 'catkin'],
    classifiers=['Programming Language :: Python',
                 'License :: OSI Approved :: Apache Software License'],
    description="Build farm used to build the ROS ecosystem's packages.",
    long_description=long_description,
    license='Apache 2.0',
)
