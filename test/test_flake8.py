# Copyright 2018 Open Source Robotics Foundation, Inc.
# Licensed under the Apache License, Version 2.0

import os
import subprocess
import sys

import pytest


@pytest.mark.flake8
@pytest.mark.linter
def test_flake8() -> None:
    # flake8 doesn't have a stable public API as of ver 6.1.0.
    # See: https://flake8.pycqa.org/en/latest/user/python-api.html
    # Calling through subprocess is the most stable way to run it.

    result = subprocess.run(
        [sys.executable, '-m', 'flake8'],
        cwd=os.path.dirname(os.path.dirname(__file__)),
        check=False,
    )
    assert 0 == result.returncode, 'flake8 found violations'
