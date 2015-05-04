*miscellaneous* jobs
====================

ROS distro cache
----------------

* The ``rosdistro-cache`` job generates the rosdistro cache for a specific ROS
  distribution.
  Since most of the other jobs use the rosdistro cache as input it is run
  automatically and pretty frequently (e.g. every five minutes).


Check slaves
------------

* The ``check_slaves`` job makes sure that slaves are automatically reenabled
  after they recovered from having not enough free disk space.


Dashboard
---------

* The ``dashboard`` job provides an overview about the status of all jobs.
  It shows the number of jobs grouped by their view and status.


Status pages
------------

The following jobs generate HTML pages to visualize the status of the package
repositories:

* The ``release-status-page`` job invokes the script
  *build_release_status_page.py*.
  The generated page shows the ROS packages of a specific ROS distribution and
  their package versions in the three repositories:

  * *building*,
  * *testing / shadow-fixed*
  * *main / ros / public*.

  Each page shows the packages and targets defined by a *release build file*.

* The ``repos-status-page`` job invokes the script
  *build_repos_status_page.py*.
  The generated page shows all packages for a set of three repositories:

  * *building*,
  * *testing / shadow-fixed*
  * *main / ros / public*.

  Each page shows the targets defined by all the release build files using
  the same *target* repository.
