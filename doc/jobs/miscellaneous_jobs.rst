*miscellaneous* jobs
====================

ROS distro cache
----------------

* The ``rosdistro-cache`` job generates the rosdistro cache for a specific ROS
  distribution.
  Since most of the other jobs use the rosdistro cache as input it is run
  automatically and pretty frequently (e.g. every five minutes).


Check agents
------------

* The ``check_agents`` job makes sure that agents are automatically reenabled
  after they recovered from having not enough free disk space.


Dashboard
---------

* The ``dashboard`` job provides an overview about the status of all jobs.
  It shows the number of jobs grouped by their view and status.


Status pages
------------

The following jobs generate HTML pages to visualize the status of the packages
/ repositories:

* The ``release-status-page`` job, generated on the farm by
  **generate_release_status_page_job.py**,
  invokes the script
  *build_release_status_page.py*.
  The generated page shows the ROS packages of a specific ROS distribution and
  their package versions in the three repositories:

  * *building*,
  * *testing / shadow-fixed*
  * *main / ros / public*.

  Each page shows the packages and targets defined by a *release build file*.

* The ``repos-status-page`` job, generated on the farm by
  **generate_repos_status_page_job.py**,
  invokes the script
  *build_repos_status_page.py*.
  The generated page shows all packages for a set of three repositories:

  * *building*,
  * *testing / shadow-fixed*
  * *main / ros / public*.

  Each page shows the targets defined by all the release build files using
  the same *target* repository.

* The ``release-compare-page`` job, generated on the farm by
  **generate_release_compare_page_job.py**,
  invokes the script
  *build_release_compare_page.py*.
  The generated page shows, for a specific pair of ROS distributions, how the versions of the
  packages released in the earlier distribution compare in the more recent distribution.

* The ``blocked-releases-page`` job, generated on the farm by
  **generate_blocked_releases_page_job.py**,
  invokes the script
  *build_blocked_releases_page.py*.
  The generated page shows, for a specific ROS distribution, which repositories from the previous
  distribution have not yet been released, and which repositories they are preventing from being
  released as a result.
