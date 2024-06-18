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


if __name__ == '__main__':
    try:
        run_module('ros_buildfarm.scripts.subprocess_reaper', run_name='__main__')
    except ImportError:
        # If the ros_buildfarm is not on the current PYTHONPATH add it using
        # the current script path as an anchor.
        sys.path.insert(
            0, os.path.dirname(os.path.dirname(__file__)))
        run_module('ros_buildfarm.scripts.subprocess_reaper', run_name='__main__')
