Ongoing operations
==================

Monitoring
----------

The administrator should check the status of the administrative jobs in the
*Manage* view in Jenkins.
Besides the administrator should always be informed from Jenkins via email when
administrative jobs fail.

The output of the ``dashboard`` job provides an overview about the status of
all jobs.
Furthermore the generated status pages (http://REPO_HOSTNAME/status_page/)
visualize the progress of the generated packages.


Manually sync packages
----------------------

The *source* and *binary* are imported into the ``building`` repository and if
the sync criteria is fulfilled automatically synced to the ``testing``
repository.
The maintainer should revisit the configured sync threshold to adjust it when
the number of released packages changes over the lifetime of a distribution.
The threshold should be set at a level below which a sync should not happen
into testing as there has been a major regression during the build.

It is the responsibility of the release manager to trigger a sync of packages
from the ``testing`` to the ``main`` repository.
This is intentionally a manual process and should be done after adequate
testing of the packages in the ``testing`` repository.

Whenever you want to sync the current state of packages for a specific ROS
distribution from the ``testing`` to the ``main`` repository you must trigger
the corresponding ``*_sync-packages-to-main`` job.
The sync to the ``main`` repository affects all architectures.


Guidelines for gating a sync to main
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

There is a manual process to go from testing to main.
We refer to this as a sync.

When you are preparing for a sync:

* Run the ``audit_rosdistro.py`` script in the ``scripts/release`` folder
  It will output text which is appropriate for posting to Discourse as a triage list.
  The ``audit_rosdistro.py`` will report all packages which are failing to build for a whole buildfile.
  
  For example: ``./scripts/release/audit_rosdistro.py https://raw.githubusercontent.com/ros-infrastructure/ros_buildfarm_config/production/index.yaml kinetic``

  * If it's failing on specific architectures, ticket it upstream and blacklist it in the config with a cross reference.
  * If it's failing on all platforms, rollback or remove the release from the distro.
* Check the list of packages comes from the status page, e.g. http://repositories.ros.org/status_page/ros_melodic_default.html
  Click “REGRESSION” to find the list of regressions, click “SYNC” to see how many packages there are to sync.
  Make sure there are no major regressions and ticket any with the maintainers.

  Note: A version downgrade is also marked as a regression since apt will not automatically install a newer package with a lower version.

* Announce the intent to sync with the above information.
  Example: https://discourse.ros.org/t/preparing-for-kinetic-sync-2020-08-20/16002/5

* After a period of time for resolving the identified issues above run the sync on Jenkins.
* Once sync is done: announce on discourse. The details of the sync is in the console output of the "sync to main" job (make sure to not take the ones that generate debug packages otherwise the package count is off by a factor 2)
* Tag the rosdistro with the format ``ROSDISTRO/YYYY-MM-DD``


Importing new upstream packages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you first setup the farm you imported upstream packages into the repository.
Sometimes upstream packages change which you want to reimport.
To do this run the `_import_upstream` job again without arguments.
No arguments means import from the default location(s).
We do this for things like new releases of the core ROS python tools.


Perform action on a set of jobs
-------------------------------

Sometimes you want to do bulk actions like disable or delete all jobs of a specific distro or just one target.
We recommend running a Groovy scripts using the script console.

The following Groovy script is a good starting point for various actions:

.. code-block:: groovy

   import hudson.model.Cause

   for (p in Jenkins.instance.allItems) {
     if (
       p.name.startsWith("PREFIX1__") ||
       p.name.startsWith("PREFIX2__") ||
       ... ||
       p.name.startsWith("PREFIXn__"))
     {
       println(p.name)

       // p.disable()
       // p.enable()

       // p.scheduleBuild(new Cause.UserIdCause())

       // p.delete()
     }
   }

This script will print only the matched job names.
You can uncomment any of the actions to disable, enable, trigger or delete these projects.

To run a Groovy script:

* Log in to Jenkins
* Click on "Manage Jenkins"
* Click on "Script Console"
* Paste the script into that console, and click "Run"

Note: Be extra careful when deleting jobs.
While you can easily regenerate the jobs, you might lose the history of these jobs.

Disable / remove a distribution / target
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you remove a distribution or target from the config the reconfigure scripts won't automatically remove the obsolete jobs.
You can use the above Groovy script as a starting point to disable / delete them.

Usually you want to disable the jobs first, wait a little bit in case you need to reenable them for another patch release, and then actually delete them.

Disable all jobs related to a specific target
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assuming that the ROS distribution is called ``lunar`` and the platform is ``Ubuntu Yakkety`` you can disable the jobs with the following prefixes:

* ``Lsrc_uY__`` which matches the Lunar source jobs for Ubuntu Yakkety.
* ``Lbin_uY64__`` which matches the Lunar binary jobs for Ubuntu Yakkety for the ``amd64`` architecture.
* ``Lrel_sync-packages-to-testing_yakkety_amd64`` which matches the management job to sync Lunar binary packages for Ubuntu Yakkety for the ``amd64`` architecture.
* ... add additional prefixes for other architectures.

If the configuration also specifies ``devel``, ``doc`` or ``pull request`` jobs for the specific target they can to be disabled too:

* ``Ldev_<key>__`` which matches the Lunar devel jobs for the given build file key.
* ``Ldoc_<key>__`` which matches the Lunar doc jobs for the given build file key.
* ``Lpr_<key>__`` which matches the Lunar PR jobs for the given build file key.

In the case of deleting the jobs the views with the same names should be empty now and can be deleted as well.
After going to specific view you can click the ``"Delete *"`` button on the left sidebar.

If your configuration also contains build files specific to the disabled target you should also disable the corresponding management jobs in the ``Manage`` view.
They will start with ``Ldev_<key>``, ``Ldoc_<key>``, ``Lrel_ <key>`` followed by the key of the build file from your config.

Disable all jobs related to a ROS distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The process is the same as for for disabling a specific target.
The prefixes are just slightly more generic to match all targets of that ROS distribution:

* ``Lsrc_`` which matches all Lunar source jobs.
* ``Lbin_`` which matches all Lunar binary jobs.
* ``Lrel_`` which matches the Lunar release related management jobs.
* ``Ldev_`` which matches the Lunar devel jobs as well as the management related jobs.
* ``Ldoc_`` which matches the Lunar doc jobs as well as the management related jobs.
* ``Lpr_`` which matches the Lunar PR jobs as well as the management related jobs.

Deleting all views related to a ROS distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you deleted all the jobs of a given ROS distribution, now all the views associated with them are empty.
You can delete them manually by going to a specific view and click the "Delete View" button on the left sidebar.
Or programmatically, using the same prefixes as the ones used to delete the jobs:

.. code-block:: groovy

  import hudson.model.Cause
  for (p in Jenkins.instance.views) {
    if (
      p.name.startsWith("PREFIX1__") ||
      p.name.startsWith("PREFIX2__") ||
      ... ||
      p.name.startsWith("PREFIXn__"))
    {
      viewOwner = Jenkins.instance.getView(p.name).getOwner();
      println("deleting view: " + p.name);
      // viewOwner.deleteView(p);
    }
  }
