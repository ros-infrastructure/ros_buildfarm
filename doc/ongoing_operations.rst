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

When preparing for a sync it is recommended to review the
*release status page*.
There are filters for viewing regressions, and what packages will sync if the
sync to main is run as well as the ability to search.

Note: A version downgrade is also marked as a regression since if users have
already installed the previous package with the higher version number apt will
not install the newer package with a lower version automatically.

Importing new upstream packages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you first setup the farm you imported upstream packages into the repository.
Sometimes upstream packages change which you want to reimport.
To do this run the `_import_upstream` job again without arguments.
No arguments means import from the default location(s).
We do this for things like new releases of the core ROS python tools.


Perform action on a set of jobs
-------------------------------

Sometimes you want to do bulk actions like disable or delete all jobs of a specific distro or architecture.
We recommend running a Groovy scripts using the script console.

The following Groovy script is a good starting point for various actions:

.. code-block:: groovy

   import hudson.model.Cause
   import java.util.regex.Matcher
   import java.util.regex.Pattern

   pattern = Pattern.compile("MYPREFIX.+")

   for (p in Jenkins.instance.projects) {
     if (!pattern.matcher(p.name).matches()) continue
     println(p.name)

     // p.disable()
     // p.enable()

     // p.scheduleBuild(new Cause.UserIdCause())

     // p.delete()
   }

This script will print only the matched job names.
You can uncomment any of the actions to disable, enable, trigger or delete these projects.

To run a Groovy script:
 * Log in to Jenkins
 * Click on "Manage Jenkins"
 * Click on "Script Console"
 * Paste the script into that console, and click "Run"

Remove a distribution / architecture
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

When you remove a distribution or architecture the reconfigure scripts won't automatically remove the obsolete jobs.
You can use the above Groovy script to delete obsolete jobs.

The associated views as well as the management jobs need to be removed manually.
If you have a job or view selected, there is a "Delete *" button on the left sidebar.
