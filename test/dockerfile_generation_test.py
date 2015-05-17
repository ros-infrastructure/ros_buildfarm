#!/usr/bin/env python3

import difflib
import filecmp
import os
import pkg_resources
import sys
import textwrap
import unittest
import yaml

from collections import OrderedDict
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO
from em import Interpreter

from ros_buildfarm.templates import _find_first_template
from ros_buildfarm.templates import _find_first_wrappers
from ros_buildfarm.templates import create_dockerfile
from ros_buildfarm.common import get_debian_package_name


def ordered_load(stream, Loader=yaml.Loader, object_pairs_hook=OrderedDict):
    """Load yaml data into an OrderedDict"""
    class OrderedLoader(Loader):
        pass

    def construct_mapping(loader, node):
        loader.flatten_mapping(node)
        return object_pairs_hook(loader.construct_pairs(node))
    OrderedLoader.add_constructor(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        construct_mapping)
    return yaml.load(stream, OrderedLoader)


class TestDockerfileGeneration(unittest.TestCase):

    def setUp(self):
        """Setup for each unittest in testcase"""

        test_path = os.path.dirname(__file__)
        sys.path.append(os.path.join(test_path, 'ros_foo'))
        sys.path.append(os.path.join(test_path, 'ros_bar'))

        base_path = '/tmp/test/ros_build/dockerfile_dir'
        if not os.path.exists(base_path):
            os.makedirs(base_path)
        self.base_path = base_path

        platform_path = os.path.join(test_path, 'platform.yaml')
        images_path = os.path.join(test_path, 'images.yaml.em')

        # Ream platform perams
        with open(platform_path, 'r') as f:
            # use safe_load instead load
            self.platform = yaml.safe_load(f)['platform']

        # Ream image perams using platform perams
        images_yaml = StringIO()
        try:
            interpreter = Interpreter(output=images_yaml)
            with open(images_path, 'r') as fh:
                interpreter.file(fh, locals=self.platform)
            images_yaml = images_yaml.getvalue()
        except Exception as e:
            print("Error processing %s" % images_path)
            raise
        finally:
            pass
            interpreter.shutdown()
            interpreter = None
        # Use ordered list
        self.images = ordered_load(images_yaml, yaml.SafeLoader)['images']

    def test_find_first_template(self):
        """Test _find_first_template function"""
        # For each image tag
        for image in self.images:

            # Get data for image
            data = dict(self.images[image])

            expected_template_package = 'ros_foo'
            data['template_name'] = os.path.join('templates', data['template_name'])
            template_package = _find_first_template(**data)

            # Test
            msg = textwrap.dedent(
                """
                The first package found to have the template_name:
                    '%s'
                as a template resource should be:
                    '%s'
                """
                % (data['template_name'], expected_template_package))
            self.assertEqual(template_package, expected_template_package, msg=msg)

    def test_find_first_wrappers(self):
        """Test _find_first_wrappers function"""
        for image in self.images:

            # Get data for image
            data = dict(self.images[image])

            expected_wrapper_scripts = {'test_wrapper.py': 'wrapper_foo\n'}
            wrapper_scripts = _find_first_wrappers(**data)

            # Test
            msg = textwrap.dedent(
                """
                The first file found:
                    '%s'
                should be the sting:
                    '%s'
                """
                % ('test_wrapper.py', 'wrapper_foo\\n'))
            self.assertEqual(wrapper_scripts, expected_wrapper_scripts, msg=msg)

    def test_create_dockerfile(self):
        """Test create_dockerfile function"""
        # For each image tag
        for image in self.images:

            # Get data for image
            data = dict(self.images[image])
            data['tag_name'] = image

            # Add platform perams
            data.update(self.platform)

            # Get debian package names for ros
            ros_packages = []
            for ros_package_name in data['ros_packages']:
                ros_packages.append(
                    get_debian_package_name(
                        data['rosdistro_name'], ros_package_name))
            data['ros_packages'] = ros_packages

            # Get path to save Docker file
            dockerfile_dir = os.path.join(self.base_path, image)
            if not os.path.exists(dockerfile_dir):
                os.makedirs(dockerfile_dir)
            data['dockerfile_dir'] = dockerfile_dir

            # generate Dockerfile
            create_dockerfile(data)

            # Get paths to Dockerfiles
            generated_dockerfile_path = os.path.join(dockerfile_dir, 'Dockerfile')
            expected_dockerfile_path = pkg_resources.resource_filename(
                'ros_foo', os.path.join('templates', 'docker_images', image, 'Dockerfile'))

            # Test
            with open(expected_dockerfile_path) as fh:
                expected_dockerfile = fh.readlines()
            with open(generated_dockerfile_path) as fh:
                generated_dockerfile = fh.readlines()
            diff = difflib.unified_diff(expected_dockerfile,
                                        generated_dockerfile,
                                        fromfile='expected', tofile='generated', lineterm='\n')
            diff = '\n' + ''.join(diff)
            msg = textwrap.dedent(
                """
                The Dockerfile generated:
                    '%s'
                does not mach the expected example:
                    '%s'
                """
                % (generated_dockerfile_path, expected_dockerfile_path))
            msg += diff
            self.assertTrue(filecmp.cmp(generated_dockerfile_path, expected_dockerfile_path), msg)

    def tearDown(self):
        """Teardown for each unittest in testcase"""
        test_path = os.path.dirname(__file__)
        sys.path.remove(os.path.join(test_path, 'ros_foo'))
        sys.path.remove(os.path.join(test_path, 'ros_bar'))

if __name__ == '__main__':
    unittest.main()
