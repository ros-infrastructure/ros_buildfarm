How to release custom packages to a forked rosdistro database?
==============================================================

* add second distribution file

* optionally update the build files to only build packages from the second
  distribution file
  (not yet implemented, requires identification of distribution files)

* releasing packages into distributions with multiple distribution files
  requires a
  [custom bloom version](https://github.com/ros-infrastructure/bloom/pull/330).
