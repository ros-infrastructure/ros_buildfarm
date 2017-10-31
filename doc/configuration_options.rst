Configuration options
=====================

The ROS build farm configuration has a similar structure than the rosdistro
specification (see `REP 143 <http://www.ros.org/reps/rep-0143.html>`_ for
details).

The configuration for the official ROS build farm configuration acts as an
example and can be found on
`GitHub (ros-infrastructure/ros_buildfarm_config) <https://github.com/ros-infrastructure/ros_buildfarm_config>`_.


Entry point yaml
----------------

This yaml file acts as the entry point to the ROS build farm configuration.
Most script require to pass the URL to this file as an argument.

The file format is specified by the following information:

* ``type: buildfarm`` identifies the yaml file as the entry point for the ROS
  build farm configuration.
* ``version: 1`` specifies the specification version of the file.

The following options are valid in version ``1``:

* ``distributions``: a dictionary mapping lowercase ROS distribution names to
  the following build files.
  The key "*default*" for a build file is hidden when being used to generate
  view / job prefixes.

  * ``release_builds``: a dictionary of release build files indexed by their
    name.
  * ``source_builds``: a dictionary of source build files indexed by their
    name.
  * ``doc_builds``: a dictionary of doc build files indexed by their name.

  All build file references can be either relative path or absolute URLs.

  * ``notification_emails``: a list of email addresses for notification about
    ROS distribution specific administrative jobs.

* ``git_ssh_credential_id``: the ID of the credential entry managed on the
  Jenkins master which is used to clone sources using Git over SSH.
  This credential id is set in the buildfarm_deployment.

* ``jenkins_url``: the URL of the Jenkins master.

* ``notification_emails``: a list of email addresses for notification about
  ROS distribution agnostic administrative jobs.

* ``prerequisites``: a dictionary containing information about repositories
  which contain the necessary tools to run the ROS build farm.
  Currently the configuration only supports Debian repositories:

  * ``debian_repositories``: a list of URLs to Debian repositories.
  * ``debian_repository_keys``: a list of PGP keys each as a multi line string.
    The order of the keys must match the repository URLs.

* ``rosdistro_index_url``: the URL to the rosdistro index yaml file.
* ``status_page_repositories``: a dictionary mapping names to a list of
  repository URLs.
  For each entry in the dictionary a
  `repos-status-page <jobs/miscellaneous_jobs#status-pages.rst>`_ is being
  generated.


Generic options in build files
------------------------------

A set of options which can be used in any build file.

* ``repositories``: additional repositories to fetch packages from.

  * ``keys``: a list of PGP keys each as a multi line string.
    The order of the keys must match the repository URLs.
  * ``urls``: a list of URLs to repositories.

* ``tag_whitelist``: a list of tags to whitelist to identify which rosdistro
  distribution files this build file should operate on.
* ``tag_blacklist``: a list of tags to blacklist to identify which rosdistro
  distribution files this build file should not operate on.

* ``targets``: a nested dictionary of targets for which packages are built.
  The first level key contains the OS name.
  The second level key contains the OS code name.
  The third level key contains the CPU architecture.
  The third level value is always empty.
  The first level key "_config" is reserved for specifying target specific
  information.

  The OS names and OS code names specified must be listed as a
  *release platform* in the corresponding rosdistro distribution file.

  A doc build file must only contain a single target.


Description of common options
-----------------------------

* **Jenkins job priorities**: a lower number means a higher priority.

  If no value is provided the generated job will not have specific priority.
  Then you should specify them using *JobGroups* through the Jenkins user
  interface.

  The job priorities of the administrative jobs are hard coded:

  * ``rosdistro-cache`` jobs: 10
  * ``check_agents`` job: 20
  * ``dashboard`` job: 20
  * ``*-status-page`` jobs: 20
  * ``reconfigure-jobs`` jobs: 30
  * ``*-trigger-jobs`` jobs: 40

  It is highly recommended to only use lower priorities for the actual jobs
  (aka higher numbers).

* **Jenkins job timeouts**: the number of minutes after which a job should be
  aborted.

* **Jenkins job label**: the label expression to restrict the execution of a
  job to a specific computer or group of machines.

* **Notification emails**: the notification about repository / package specific
  job statuses can be send to:

  * a list of statically configure email addresses.
  * a list of maintainer email addresses extracted from the package manifests
    being processed.
  * a list of developer email addresses extracted from version control system.

* **Package / repository white- / blacklisting**: if no whitelist is specified
  all existing items are being used.
  The blacklist is applied after the whitelist which means if an item is in
  both lists it is being *excluded*.

* **Skip ignored packages / repositories**: by default jobs are still being
  generated for blacklisted (or not whitelisted) items but these jobs are
  disabled.
  To avoid generating these jobs to be generated set this flag to ``true``.

* **Credential ID**: the ID of the credential entry managed on the Jenkins
  master which is commonly used to upload artifacts to another host.
  This credential id is set in the buildfarm_deployment.


Specific options in release build files
---------------------------------------

This yaml file defines the configuration for *release* jobs.

The file format is specified by the following information:

* ``type: release-build`` identifies the yaml file as a *release build file*.
  build farm configuration.
* ``version: 2`` specifies the specification version of the file.

The following options are valid in version ``2`` (beside the generic options):

* ``abi_incompatibility_assumed``: a boolean flag if binary packages should
  trigger downstream packages for rebuilding them (default: ``false``).
  For ROS 1 this flag must always be ``true``.

* ``jenkins_binary_job_label``: the label expression for *binary* jobs
  (default: ``buildagent || <ROSDISTRO_NAME>_binarydeb_<BUILD_FILE_NAME>``).
* ``jenkins_binary_job_priority``: the job priority of *binary* jobs.
* ``jenkins_binary_job_timeout``: the job timeout for *binary* jobs.
* ``jenkins_source_job_label``: the label expression for *source* jobs
  (default: ``buildagent || <ROSDISTRO_NAME>_sourcedeb``).
* ``jenkins_source_job_priority``: the job priority of *source* jobs.
* ``jenkins_source_job_timeout``: the job timeout for *source* jobs.

* ``notifications``: a dictionary with the following keys:

  * ``emails``: a list of static email addresses.
  * ``maintainers``: a boolean flag if the maintainers should be notified
    (default: ``false``).

* ``package_whitelist``: a list of package names to whitelist.
* ``package_blacklist``: a list of package names to blacklist.
* ``skip_ignored_packages``: a boolean flag if jobs for blacklisted (or not
  whitelisted) packages should not be generated (default: ``false``).

* ``sync``: the sync criteria which must be fulfilled before syncing from
  ``building`` to ``testing``.

  * ``package_count``: the minimum number of *binary* packages which must be
    available.
  * ``packages``: a list of package names which must be available.

* ``target_queue``: the path where incoming changes to the target repository
  are being queued (default: ``/var/repos/ubuntu/building/queue``).

* ``target_repository``: the target repository to push built *source* and
  *binary* packages to.
  This should always refer to the *building* repository.

* ``upload_credential_id``: the ID of the credential to upload the built
  packages to the repository host.


Specific options in source build files
---------------------------------------

This yaml file defines the configuration for *devel* jobs.

The file format is specified by the following information:

* ``type: source-build`` identifies the yaml file as a *source build file*.
* ``version: 2`` specifies the specification version of the file.

The following options are valid in version ``2`` (beside the generic options):

* ``jenkins_commit_job_priority``: the job priority of *devel* jobs.
* ``jenkins_job_label``: the label expression for both *devel* and
  *pull request* jobs (default:
  ``buildagent || <ROSDISTRO_NAME>_devel_<BUILD_FILE_NAME>``).
* ``jenkins_job_timeout``: the job timeout for both *devel* and *pull request*
  jobs.
* ``jenkins_pull_request_job_priority``: the job priority of *pull request*
  jobs.

* ``notifications``: a dictionary with the following keys:

  * ``compiler_warnings``: boolean flag if compiler warnings should mark a job
    as unstable (default: ``false``)
  * ``committers``: a boolean flag if the committers should be notified.
  * ``emails``: a list of static email addresses.
  * ``maintainers``: a boolean flag if the maintainers should be notified.
  * ``pull_requests``: boolean flag if notifications should be sent for pull
    request jobs (default: ``false``)

* ``repository_whitelist``: a list of repository names to whitelist.
* ``repository_blacklist``: a list of repository names to blacklist.
* ``skip_ignored_repositories``: a boolean flag if jobs for blacklisted (or not
  whitelisted) repositories should not be generated (default: ``false``).

* ``test_commits``: a dictionary to decide if *devel* jobs should be generated.

  * ``default``: a boolean flag defining the default value for repositories
    which do not specify the value explicitly (default: ``None``).
  * ``force``: a boolean flag enforcing the value for all repositories if set
    to either ``true`` or ``false`` (default: ``None``).

* ``test_pull_requests``: a dictionary to decide if *pull request* jobs should
  be generated.

  * ``default``: a boolean flag as described for *test_commits*.
  * ``force``: a boolean flag as described for *test_commits*.

The following options are valid as keys in the ``_config`` dict under
``targets``:

* ``custom_rosdep_urls``: a list of URLs containing rosdep sources.list.d entry
  files that are downloaded into /etc/ros/rosdep/sources.list.d at the beginning
  of the devel job after running *rosdep init*.
  Note that *rosdep init* will add the 20-default.list file from the public
  rosdistro by default.
  To override this, add an entry to this list corresponding to the
  20-default.list file from your forked rosdistro repository.

Specific options in doc build files
---------------------------------------

This yaml file defines the configuration for *doc* jobs.

The file format is specified by the following information:

* ``type: doc-build`` identifies the yaml file as a *doc build file*.
* ``version: 2`` specifies the specification version of the file.

The following options are valid in version ``2`` (beside the generic options):

* ``jenkins_job_priority``: the job priority of *doc* jobs.
* ``jenkins_job_label``: the label expression for both *doc* jobs (default:
  ``buildagent || <ROSDISTRO_NAME>_doc_<BUILD_FILE_NAME>``).
* ``jenkins_job_timeout``: the job timeout for *doc* jobs.

* ``notifications``: a dictionary with the following keys:

  * ``committers``: a boolean flag if the committers should be notified (only
    allowed if ``released_packages`` is ``false``).
  * ``emails``: a list of static email addresses.
  * ``maintainers``: a boolean flag if the maintainers should be notified (only
    allowed if ``released_packages`` is ``false``).

* ``package_whitelist``: a list of package names to whitelist (only allowed if
  ``released_packages`` is ``true``).
* ``package_blacklist``: a list of package names to blacklist (only allowed if
  ``released_packages`` is ``true``).

* ``released_packages``: a boolean flag if released packages without *doc*
  entries should be documented (default: ``false``).
  If set to ``false`` a job is being generated for every repository with a
  *doc* entry and *rosdoc_lite* is being invoked in every package in that
  repository.
  If set to ``true`` a single job is being generated to extract the metadata
  from the released package manifests.

* ``repository_whitelist``: a list of repository names to whitelist (only
  allowed if ``released_packages`` is ``false``).
* ``repository_blacklist``: a list of repository names to blacklist (only
  allowed if ``released_packages`` is ``false``).
* ``skip_ignored_repositories``: a boolean flag if jobs for blacklisted (or not
  whitelisted) repositories should not be generated (default: ``false``) (only
  allowed if ``released_packages`` is ``false``).

* ``upload_credential_id``: the ID of the credential to upload the built
  packages to the repository host.
* ``upload_host``: The hostname to use to rsync the resultant files.
  This should match the config ``upload::docs::host`` in the buildfarm_deployment_config.
  The default is ``repo``.
* ``upload_root``: The root directory on the server to use to rsync the resultant files.
  This should match the config ``upload::docs::root`` in the buildfarm_deployment_config.
  The default is ``/var/repos/docs``.
* ``upload_user``: The username to use to rsync the resultant files.
  This should match the config ``upload::docs::user`` in the buildfarm_deployment_config.
  The default is ``jenkins-agent``

The following options are valid as keys in the ``_config`` dict under
``targets``:

* ``custom_rosdep_urls``: a list of URLs containing rosdep sources.list.d entry
  files that are downloaded into /etc/ros/rosdep/sources.list.d at the beginning
  of the doc job after running *rosdep init*.
  Note that *rosdep init* will add the 20-default.list file from the public
  rosdistro by default.
  To override this, add an entry to this list corresponding to the
  20-default.list file from your forked rosdistro repository.
