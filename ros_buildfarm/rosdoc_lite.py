from __future__ import print_function

import sys

import yaml


# this is reimplemented here since rosdoc_lite can not be used with Python 3
def get_generator_output_folders(pkg_rosdoc_config_file, pkg_name):
    output_folders = {}
    if pkg_rosdoc_config_file:
        with open(pkg_rosdoc_config_file, 'r') as h:
            content = h.read()
        try:
            data = yaml.safe_load(content)
        except Exception as e:
            print("WARNING: package '%s' has an invalid rosdoc config: %s" %
                  (pkg_name, e), file=sys.stderr)
        else:
            if not isinstance(data, list):
                print("WARNING: package '%s' has an invalid rosdoc config" %
                      pkg_name, file=sys.stderr)
            else:
                for item in data:
                    if 'builder' not in item:
                        print("WARNING: package '%s' has an invalid rosdoc config "
                              "- missing builder key" % pkg_name, file=sys.stderr)
                        continue
                    if item.get('output_dir'):
                        output_folders[item['builder']] = item['output_dir']
    return output_folders
