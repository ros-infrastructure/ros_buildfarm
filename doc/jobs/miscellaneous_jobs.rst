*miscellaneous* jobs
====================

Status pages
------------

The following scripts generate HTML pages to visualize the status of the
package repositories:

* ``build_release_status_page.py`` shows the ROS packages of a specific ROS
  distribution and their package versions in the three repositories:

  * *building*,
  * *testing / shadow-fixed*
  * *main / ros / public*.

  Each page shows the packages and targets defined by a release build file.

* ``build_repos_status_page.py`` shows all packages for a set of three
  repositories:

  * *building*,
  * *testing / shadow-fixed*
  * *main / ros / public*.

  Each page shows the targets defined by all the release build files using
  the building repository as a target repository.


ROS distro cache
----------------

* ``rosdistro_cache`` generates the rosdistro cache for a specific ROS
  distribution.


Synchronize packages between repositories
-----------------------------------------

TODO


Import third-party packages into repositories
---------------------------------------------

TODO


Regenerate jobs automatically
-----------------------------

TODO


Trigger jobs / retrigger failing jobs
-------------------------------------

TODO
