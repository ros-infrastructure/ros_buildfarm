^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package ros_buildfarm
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Forthcoming
-----------
* fix navigation bar in the wiki to list the packages which are part of a meta package (`#193 <https://github.com/ros-infrastructure/ros_buildfarm/pull/193>`_)
* add check if any upstream project is in progress to prevent notification email for jobs known to fail and being retriggered anyway (`#194 <https://github.com/ros-infrastructure/ros_buildfarm/pull/194>`_)
* add subsections for "build", "build tests" and "run tests" in devel jobs (`#195 <https://github.com/ros-infrastructure/ros_buildfarm/pull/195>`_)
* fix environment for tests in devel and pull request jobs (`#196 <https://github.com/ros-infrastructure/ros_buildfarm/pull/196>`_)
* add "Queue" view to see all queued builds without the overhead of a job list (`#197 <https://github.com/ros-infrastructure/ros_buildfarm/pull/197>`_)
* fix reconfigure devel views (`#200 <https://github.com/ros-infrastructure/ros_buildfarm/pull/200>`_)
* wrapper script for "git clone" to retry in case of network issues (`#201 <https://github.com/ros-infrastructure/ros_buildfarm/pull/201>`_)
* catch 'Unable to locate package' apt-get error and retry (`#204 <https://github.com/ros-infrastructure/ros_buildfarm/pull/204>`_)
* fix test environment for workspaces with only plain CMake packages (`#205 <https://github.com/ros-infrastructure/ros_buildfarm/pull/205>`_)
* fix unnecessary triggering of devel jobs using Mercurial (`#206 <https://github.com/ros-infrastructure/ros_buildfarm/pull/206>`_)
* fix special case in doc jobs where metapackage dependencies was None (`#207 <https://github.com/ros-infrastructure/ros_buildfarm/pull/207>`_)
* remove non-existing job urls in generated manifest.yaml files (`#208 <https://github.com/ros-infrastructure/ros_buildfarm/pull/208>`_)
* retry on known apt-get errors when downloading sourcedeb files (`#209 <https://github.com/ros-infrastructure/ros_buildfarm/pull/209>`_)
* fix groovy script to generate views (`#210 <https://github.com/ros-infrastructure/ros_buildfarm/pull/210>`_)
* retry when docker fails to pull base image (`#212 <https://github.com/ros-infrastructure/ros_buildfarm/pull/212>`_)

1.0.0 (2016-02-01)
------------------
* This is the first stable release. Please look at the git commit log for historic information.
