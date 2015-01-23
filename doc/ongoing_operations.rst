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
