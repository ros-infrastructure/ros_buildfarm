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

* ``build_environment_variables``: a dictionary containing environment
  variables which will be inserted into binarydeb build containers before
  package dependencies are installed using Dockerfile ``ENV`` directives.
  Note that yaml will turn bare words like ``yes`` into boolean values so it
  is recommended to quote values to avoid interpretation.

* ``project_authorization_xml``: an XML blob which will be nested within a
  ``<hudson.security.AuthorizationMatrixProperty>`` in job builds.
  This property is defined for all build files but as of `#737`_ is only
  implemented for **CI jobs**.

  .. _#737: https://github.com/ros-infrastructure/ros_buildfarm/pull/737

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

  A doc build file of **rosdoc_lite**, **released_manifest** or **make_target**
  documentation type can only be built for a single target and thus it must not
  specificy more than one.

  A doc build file of **docker_build** documentation type is built for the
  platform the associated docker image is based on, therefore no targets can
  be specified.

* ``shared_ccache``: when set to ``true``, the executing user's ccache directory
  is shared in the build container, which is configured to use ccache where
  appropriate (default: ``false``).

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

* **Package 'ignore' listing**: The process for blacklisting packages also
  affects the recursive dependencies of those packages.
  The ignore list does not carry on to downstream packages.
  A package using this option will require all downstream dependencies to patch
  away the dependency.
  Like the blacklist, the ignore list is applied after the whitelist.

* **Skip ignored packages / repositories**: by default jobs are still being
  generated for blacklisted (or not whitelisted) items but these jobs are
  disabled.
  To avoid generating these jobs to be generated set this flag to ``true``.

* **Credential ID**: the ID of the credential entry managed on the Jenkins
  master which is commonly used to upload artifacts to another host.
  This credential id is set in the buildfarm_deployment.

* **Upload destination credential ID**: the ID of the credential entry managed
  on the Jenkins master which contains the destination information used to
  upload artifacts to another host.
  This credential id is set in the buildfarm_deployment.
  At present, this value is only used for RPM jobs.


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

* ``build_tool``: the build tool to use. The following are valid values:

  * ``catkin_make_isolated`` (default)
  * ``colcon``

* ``build_tool_args``: arbitrary arguments passed to the build tool.

* ``build_tool_test_args``: arbitrary arguments passed to the build tool during
  testing.

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

* ``test_abi``: a dictionary to decide if *abi checker* is going to be run in
  PR and devel jobs
  * ``default``: a boolean flag as described for *test_commits*.
  * ``force``: a boolean flag as described for *test_commits*.

* ``tests_require_gpu``: a dictionary to indicate if software tests needs gpu
  support to run correctly.
  * ``default``: a boolean flag as described for *test_commits*.

* ``collate_test_stats``: a boolean flag (default: ``False``) controlling
  whether test statistics collation should be enabled for devel jobs.
  Enabling this will add post-build steps to jobs that collate test statistics
  for historical builds, serialize those to yaml snippets and copy those
  snippets to the ``repo`` host.
  A special macro in the ROS wiki will then render those test results as part of
  the auto-generated *Package Header*.

* ``benchmark_patterns``: a list of file patterns relative to the Jenkins
  workspace where benchmark result files are expected to be found.

* ``benchmark_schema``: a JSON or XML schema which describes the structure of
  the files referenced by the ``benchmark_patterns`` value, which is required
  when this option is specified.

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

* ``canonical_base_url``: The canonical base URL of the generated documentation.
  If set a canonical URL will be added to all HTML files in the form of
  ``<base-url>/<distro-name>/api/<package-name>``.
* ``documentation_type``: The option distinguishes different documentation
  jobs. The following are valid values and describe their semantic:

  * ``rosdoc_lite`` (default): Generates documentation jobs for each
    repository. Each job invokes ``rosdoc_lite`` for all packages in the
    repository.
  * ``released_manifest``: Generates some minimal documentation for released
    packages which don't have their own documentation job.
  * ``make_target``: Invokes ``make html`` in the ``doc`` subdirectory for a
    set of repositories. See ``doc_repositories`` to configure the
    repositories.
  * ``docker_build``: Commits documentation content to be pushed to an
    ``upload_repository_url`` generated from a set of repositories by
    running Docker containers provided by each. See ``doc_repositories``
    to configure the repositories. See *doc* jobs documentation to learn
    about the expected Dockerfile structure.

* ``doc_repositories``: a list of repository URLs, or a dictionary of repository
  URLs and branches (used when the ``documentation_type`` is set to ``make_target``
  or ``docker_build``).  When the list form is used, the default branch from each
  repository is always used.  When the dictionary form is used, it should have
  the following structure:

::
   repo_name:
     url: <url_to_doc_repository>
     branch: <branch_name_to_use>

* ``install_apt_packages``: a list of packages to be installed with apt (only
  allowed when the ``documentation_type`` is set to ``make_target``).
* ``install_pip_packages``: a list of packages to be installed with pip (only
  allowed when the ``documentation_type`` is set to ``make_target``).
* ``jenkins_job_priority``: the job priority of *doc* jobs.
* ``jenkins_job_label``: the label expression for both *doc* jobs (default:
  ``buildagent || <ROSDISTRO_NAME>_doc_<BUILD_FILE_NAME>``).
* ``jenkins_job_timeout``: the job timeout for *doc* jobs.

* ``build_tool``: the build tool to use. The following are valid values:

  * ``catkin_make_isolated`` (default)
  * ``colcon``

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

The following options are valid for all ``documentation_type`` values:

* ``upload_credential_id``: the ID of the credential to upload the built
  packages to the repository host.

The following options are valid for ``documentation_type`` values other
than ``docker_build``:

* ``upload_host``: The hostname to use to rsync the resultant files.
  This should match the config ``upload::docs::host`` in the buildfarm_deployment_config.
  The default is ``repo``.
* ``upload_root``: The root directory on the server to use to rsync the resultant files.
  This should match the config ``upload::docs::root`` in the buildfarm_deployment_config.
  The default is ``/var/repos/docs``.
* ``upload_user``: The username to use to rsync the resultant files.
  This should match the config ``upload::docs::user`` in the buildfarm_deployment_config.
  The default is ``jenkins-agent``

The following options are valid when ``documentation_type`` is set to
``docker_build``:

* ``upload_repository_url``: The URL of the git repository to push resultant
  files to.

The following options are valid as keys in the ``_config`` dict under
``targets``:

* ``custom_rosdep_urls``: a list of URLs containing rosdep sources.list.d entry
  files that are downloaded into /etc/ros/rosdep/sources.list.d at the beginning
  of the doc job after running *rosdep init*.
  Note that *rosdep init* will add the 20-default.list file from the public
  rosdistro by default.
  To override this, add an entry to this list corresponding to the
  20-default.list file from your forked rosdistro repository.

Specific options in CI build files
----------------------------------

This yaml file defines the configuration for *CI* jobs.

The file format is specified by the following information:

* ``type: ci-build`` identifies the yaml file as a *CI build file*.
* ``version: 1`` specifies the specification version of the file.

The following options are valid in version ``1`` (beside the generic options):

* ``build_tool``: the build tool to use.
  The following are valid values:

  * ``catkin_make_isolated``
  * ``colcon`` (default)

* ``build_tool_args``: arbitrary arguments passed to the build tool.

* ``build_tool_test_args``: arbitrary arguments passed to the build tool during
  testing.

* ``install_packages``: a list of packages which should be installed by default
  before any of the dependencies necessary to build the packages in the
  workspace.
  Since not all packages in the workspace are necessarily ROS packages, rosdep
  may be unable to detect and install the prerequisites for those packages, so
  those prerequisite packages may need to be listed here.

* ``jenkins_job_priority``: the job priority of *CI* jobs.

* ``jenkins_job_schedule``: the schedule on which to run the nightly *CI* job.
  For example, to run the nightly build at 11 PM each night, a value of
  ``0 23 * * *`` may be used.

* ``jenkins_job_timeout``: the job timeout for *CI* jobs.

* ``jenkins_job_upstream_triggers``: names of other CI jobs which, when
  built with a stable or unstable result, should trigger this job to be built.

* ``jenkins_job_weight``: the number of executors on a worker which are
  required to execute the job.
  Default is ``1``.
  Uses the Jenkins Heavy Job plugin.

* ``package_selection_args``: package selection arguments passed to ``colcon``
  to specify which packages should be built and tested.
  Note that ``colcon`` is always used to select packages even when
  ``build_tool`` specifies something other else.

* ``repos_files``: the list of ``.repos`` files to use by default when creating
  a workspace to build.

* ``repository_names``: the names of repositories in the rosdistro to be
  checkout into the workspace with their branch specified in the ``source``
  entry.

* ``archive_files``: a list of workspace-relative paths and/or glob expressions to
  files to be kept as additional build artifacts.

* ``show_images``: a dictionary of lists, where the key is the title of a group
  of image artifacts to display and the list contains workspace-relative paths
  to images generated by each build which should be displayed on the build's
  summary page.
  These images will automatically be added to the artifacts for each build.

* ``show_plots``: a dictionary of lists, where the key is the title of the
  plot group and the list contains plot definitions comprised of:

  * ``title``: the title of the plot.
  * ``description``: the description of the plot. This might contains HTML such
    as the tags: <b>, <li>, <ul>, etc.
  * ``y_axis_label``: (optional) a label for the y-axis.
  * ``master_csv_name``: the name of the CSV file in which to aggregate the
    results on the Jenkins master.
    It must be unique among all plot instances on the same Jenkins master.
  * ``style``: the type of plot used to display the data.
    Supported values: area, bar, bar3d, line, lineSimple, line3d, stackedArea,
    stackedBar, stackedBar3d, waterfall
  * ``y_axis_exclude_zero``: a boolean flag which indicates when to exclude an
    implicit zero value from the y-axis.
  * ``y_axis_minimum``: Minimum y-axis value.
  * ``y_axis_maximum``: Maximum y-axis value.
  * ``num_builds``: Number of builds back to show on this plot (default: ``0``
    which means all builds).
  * ``data_series``: a list of data series definitions comprised of:

    * ``data_file``: a path pattern relative to the workspace root to a file
      containing the data.
    * ``data_type``: the type of file to which ``data_file`` refers.
      Supported values: csv, xml, properties
    * ``selection_flag``: strategy used to identify which data from the
      ``data_file`` should be extracted and plotted.
      Supported values: OFF, INCLUDE_BY_STRING, EXCLUDE_BY_STRING,
      INCLUDE_BY_COLUMN, EXCLUDE_BY_COLUMN
    * ``selection_value``: specific criteria used for selection.
      The meaning of this value differs based on ``selection_flag``.
      For example, when INCLUDE_BY_COLUMN is used, this value should specify
      which column number to include (1-indexed).
      For \*_BY_STRING, the, this value should specify the column name.
      For EXCLUDE\_\*, the logic is inverted and all discovered columns EXCEPT
      those matching this value are included.
    * ``url``: Hyperlink URL to redirect when a point is clicked.

* ``benchmark_patterns``: a list of file patterns relative to the Jenkins
  workspace where benchmark result files are expected to be found.

* ``benchmark_schema``: a JSON or XML schema which describes the structure of
  the files referenced by the ``benchmark_patterns`` value, which is required
  when this option is specified.

* ``skip_rosdep_keys``: a list of rosdep keys which should be ignored when
  rosdep is invoked to resolve package dependencies.

* ``test_branch``: branch to attempt to checkout and merge in each repository
  before running the job.

* ``underlay_from_ci_jobs``: names of other CI jobs which should be used
  as an underlay to this job.
