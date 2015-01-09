#!/usr/bin/env python3

import subprocess
import sys


def main(argv=sys.argv[1:]):
    assert len(argv) < 2
    dockerfile = argv[0] if len(argv) == 1 else 'Dockerfile'
    sys.stdout.write("Get base image name from Dockerfile '%s': " % dockerfile)
    base_image = get_base_image_from_dockerfile(dockerfile)
    print(base_image)
    return call_docker_pull(base_image)


def get_base_image_from_dockerfile(dockerfile):
    with open(dockerfile, 'r') as h:
        content = h.read()
    lines = content.splitlines()
    from_prefix = 'FROM '
    for line in lines:
        if line.startswith(from_prefix):
            return line[len(from_prefix):]
    assert False, \
        "Could not find a line starting with '%s' in the Dockerfile '%s'" % \
        (from_prefix, dockerfile)


def call_docker_pull(base_image):
    cmd = ['docker', 'pull', base_image]
    print('Check docker base image for updates: %s' % ' '.join(cmd))
    return subprocess.call(cmd, stderr=subprocess.STDOUT)


if __name__ == '__main__':
    sys.exit(main())
