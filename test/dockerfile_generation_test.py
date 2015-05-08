#!/usr/bin/env python3

import argparse
import filecmp
import os
import pkg_resources
import sys
import unittest

from ros_buildfarm.templates import _find_first_template
from ros_buildfarm.templates import _find_first_wrappers
from ros_buildfarm.templates import create_dockerfile

from ros_buildfarm.docker_common import DockerfileArgParser


class TestDockerfileGeneration(unittest.TestCase):

    def setUp(self):
        """Setup for each unittest in testcase"""
        args = ['--template_packages', 'ros_foo', 'ros_bar',
                '--rosdistro-name', 'indigo',
                '--os-name', 'ubuntu',
                '--os-code-name', 'trusty',
                '--arch', 'amd64',
                '--dockerfile-dir', '/tmp/foo',
                '--packages', 'roscpp']

        self.parser = DockerfileArgParser()
        # generate data for config
        self.data = self.parser.parse(args)

        # template_name is specified relative to the templates folder in the template_packages
        template_name = 'docker_images/test.Dockerfile.em'
        self.template_name = template_name

        dockerfile_dir = '/tmp/test/ros_build/dockerfile_dir'
        if not os.path.exists(dockerfile_dir):
            os.makedirs(dockerfile_dir)
        self.dockerfile_dir = dockerfile_dir

        test_path = os.path.dirname(__file__)
        sys.path.append(os.path.join(test_path, 'ros_foo'))
        sys.path.append(os.path.join(test_path, 'ros_bar'))

    def test_find_first_template(self):
        """Test _find_first_template function"""
        expected_template_package = 'ros_foo'
        template_name = os.path.join('templates', self.template_name)
        template_package = _find_first_template(template_name, **self.data)

        msg = "\nThe first package found to have the template_name: \
        '%s' as a template resource should be: '%s'" % (
            self.template_name, expected_template_package)
        self.assertEqual(template_package, expected_template_package, msg=msg)

    def test_find_first_wrappers(self):
        """Test _find_first_wrappers function"""
        expected_wrapper_scripts = {'test_wrapper.py': 'wrapper_foo\n'}
        template_name = os.path.join('templates', self.template_name)
        wrapper_scripts = _find_first_wrappers(self.data)

        msg = "\nThe first %s file found should be the sting: '%s'" % (
            'test_wrapper.py', 'wrapper_foo\\n')
        self.assertEqual(wrapper_scripts, expected_wrapper_scripts, msg=msg)

    def test_create_dockerfile(self):
        """Test create_dockerfile function"""
        expected_dockerfile_path = pkg_resources.resource_filename(
            'ros_foo', 'templates/docker_images/test.Dockerfile')
        create_dockerfile(self.template_name, self.data, self.dockerfile_dir)
        generated_dockerfile_path = os.path.join(self.dockerfile_dir, 'Dockerfile')

        msg = "\nThe Dockerfile generated: %s does not mach the expected example: %s" % (
            generated_dockerfile_path, expected_dockerfile_path)
        self.assertTrue(filecmp.cmp(generated_dockerfile_path, expected_dockerfile_path))

    def tearDown(self):
        """Teardown for each unittest in testcase"""
        test_path = os.path.dirname(__file__)
        sys.path.remove(os.path.join(test_path, 'ros_foo'))
        sys.path.remove(os.path.join(test_path, 'ros_bar'))

if __name__ == '__main__':
    unittest.main()
