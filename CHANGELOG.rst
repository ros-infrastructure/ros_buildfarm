^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Changelog for package ros_buildfarm
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1.1.0 (2016-03-18)
------------------
* New features

  * add Wily and Xenial support (`#223 <https://github.com/ros-infrastructure/ros_buildfarm/pull/223>`_, `#225 <https://github.com/ros-infrastructure/ros_buildfarm/pull/225>`_)
  * add support for Debian (`#252 <https://github.com/ros-infrastructure/ros_buildfarm/pull/252>`_)
  * add support for ARM64 on Ubuntu (`#246 <https://github.com/ros-infrastructure/ros_buildfarm/pull/246>`_)
  * extract compiler warnings for devel/pr jobs (`#217 <https://github.com/ros-infrastructure/ros_buildfarm/pull/217>`_)
  * merge branch before building pull request job (`#219 <https://github.com/ros-infrastructure/ros_buildfarm/pull/219>`_)
  * reconfigure release jobs when the rosdistro cache gets an updated manifest (`#239 <https://github.com/ros-infrastructure/ros_buildfarm/pull/239>`_)
  * add support to run devel/pr job with e.g. Travis (`#264 <https://github.com/ros-infrastructure/ros_buildfarm/pull/264>`_)

* Improvements

  * add check if any upstream project is in progress to prevent notification email for jobs known to fail and being retriggered anyway (`#194 <https://github.com/ros-infrastructure/ros_buildfarm/pull/194>`_)
  * add subsections for "build", "build tests" and "run tests" in devel jobs (`#195 <https://github.com/ros-infrastructure/ros_buildfarm/pull/195>`_)
  * add "Queue" view to see all queued builds without the overhead of a job list (`#197 <https://github.com/ros-infrastructure/ros_buildfarm/pull/197>`_)
  * wrapper script for "git clone" to retry in case of network issues (`#201 <https://github.com/ros-infrastructure/ros_buildfarm/pull/201>`_)
  * retry on known apt-get errors when downloading sourcedeb files (`#209 <https://github.com/ros-infrastructure/ros_buildfarm/pull/209>`_)
  * retry when docker fails to pull base image (`#212 <https://github.com/ros-infrastructure/ros_buildfarm/pull/212>`_)
  * use groovy to reconfigure doc views (`#224 <https://github.com/ros-infrastructure/ros_buildfarm/pull/224>`_)
  * add subsection in doc jobs for better outline (`#227 <https://github.com/ros-infrastructure/ros_buildfarm/pull/227>`_)
  * output rsync stats (`#230 <https://github.com/ros-infrastructure/ros_buildfarm/pull/230>`_)
  * always update the depends_on entry (`#231 <https://github.com/ros-infrastructure/ros_buildfarm/pull/231>`_)
  * generate package specific notifications (`#247 <https://github.com/ros-infrastructure/ros_buildfarm/pull/247>`_)
  * allow overriding manual question with '-y' (`#260 <https://github.com/ros-infrastructure/ros_buildfarm/pull/260>`_)
  * disable pager for git log command (`# <https://github.com/ros-infrastructure/ros_buildfarm/pull/263>`_)

* Fixes

  * fix navigation bar in the wiki to list the packages which are part of a meta package (`#193 <https://github.com/ros-infrastructure/ros_buildfarm/pull/193>`_)
  * fix environment for tests in devel and pull request jobs (`#196 <https://github.com/ros-infrastructure/ros_buildfarm/pull/196>`_)
  * fix reconfigure devel views (`#200 <https://github.com/ros-infrastructure/ros_buildfarm/pull/200>`_)
  * catch 'Unable to locate package' apt-get error and retry (`#204 <https://github.com/ros-infrastructure/ros_buildfarm/pull/204>`_)
  * fix test environment for workspaces with only plain CMake packages (`#205 <https://github.com/ros-infrastructure/ros_buildfarm/pull/205>`_)
  * fix unnecessary triggering of devel jobs using Mercurial (`#206 <https://github.com/ros-infrastructure/ros_buildfarm/pull/206>`_)
  * fix special case in doc jobs where metapackage dependencies was None (`#207 <https://github.com/ros-infrastructure/ros_buildfarm/pull/207>`_)
  * remove non-existing job urls in generated manifest.yaml files (`#208 <https://github.com/ros-infrastructure/ros_buildfarm/pull/208>`_)
  * fix groovy script to generate views (`#210 <https://github.com/ros-infrastructure/ros_buildfarm/pull/210>`_)
  * use ccache from source for older distros (`#216 <https://github.com/ros-infrastructure/ros_buildfarm/pull/216>`_, `#241 <https://github.com/ros-infrastructure/ros_buildfarm/pull/241>`_)
  * allow empty package entries (which are not lists) (`#221 <https://github.com/ros-infrastructure/ros_buildfarm/pull/221>`_)
  * fix creating views (`#222 <https://github.com/ros-infrastructure/ros_buildfarm/pull/222>`_)
  * fix catkin doc job (`#228 <https://github.com/ros-infrastructure/ros_buildfarm/pull/228>`_)
  * use same os_codename to generate Dockerfile for dev jobs (`#229 <https://github.com/ros-infrastructure/ros_buildfarm/pull/229>`_)
  * fix apt-get retry logic (`#232 <https://github.com/ros-infrastructure/ros_buildfarm/pull/232>`_)
  * maintain pull request data when reconfiguring job using groovy (`#236 <https://github.com/ros-infrastructure/ros_buildfarm/pull/236>`_)
  * fix devel and doc reconfiguration if cache is behind (`#240 <https://github.com/ros-infrastructure/ros_buildfarm/pull/240>`_)
  * maintain the job order when reconfiguring using Groovy (`#242 <https://github.com/ros-infrastructure/ros_buildfarm/pull/242>`_)
  * always apt-get update in devel jobs (`#244 <https://github.com/ros-infrastructure/ros_buildfarm/pull/244>`_)
  * use build, run and test dependencies for topological order (`#245 <https://github.com/ros-infrastructure/ros_buildfarm/pull/245>`_)
  * rebuild dependency graph after reconfiguring jobs (`#251 <https://github.com/ros-infrastructure/ros_buildfarm/pull/251>`_)
  * fix script generation with Python 2 (`#259 <https://github.com/ros-infrastructure/ros_buildfarm/pull/259>`_)
  * fix wrapper scripts when being installed (`#261 <https://github.com/ros-infrastructure/ros_buildfarm/pull/261>`_)

1.0.0 (2016-02-01)
------------------
* This is the first stable release. Please look at the git commit log for historic information.
