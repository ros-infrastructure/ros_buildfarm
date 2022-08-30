#!/usr/bin/env python3

# Copyright 2022 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from runpy import run_module
import sys

try:
    from ros_buildfarm import __version__
except ImportError:
    sys.path.insert(
        0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


if __name__ == '__main__':
    run_module('ros_buildfarm.wrapper.apt', run_name='__main__')
