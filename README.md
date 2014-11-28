ros_buildfarm
=============

Scripts and templates to generate Jenkins jobs or alternatively scripts to run
jobs locally. The [doc](doc/index.rst) folder contains more information.

You will need a set of configuration files, e.g. from the
[ros_buildfarm_config](https://github.com/ros-infrastructure/ros_buildfarm_config)
repository.

To provision a Jenkins master, multiple slaves and additional services like an
apt repository and a webserver to host the generated documention you might want
to use the
[buildfarm_deployment](https://github.com/ros-infrastructure/buildfarm_deployment)

You will need the following dependencies:

* a forked version of [jenkinsapi](https://github.com/dirk-thomas/jenkinsapi/tree/feature/config_view)
* a forked version of [rosdistro](https://github.com/ros-infrastructure/rosdistro/tree/rep143)



Example deployment
==================

This assumes you have setup

Buildfarm configuration management
----------------------------------

Before launching you will need to have a buildfarm configuration.

Fork ros_buildfarm_config
,,,,,,,,,,,,,,,,,,,,,,,,,

Fork [ros_buildfarm_config](https://github.com/ros-infrastructure/ros_buildfarm_config)

Edit it as follows:
 * update the jenkins url `jenkins_url`
 * update the maintainer contact information `notification_emails`(This is important otherwise you may send someone a lot of incorrect emails!)
 * If you are using a custom rosdistro edit `rosdistro_index_url`
 * if you are using a different set of bootstrap packages update the `prerequisites` including `debian_repositories` and `debian_repository_keys`

Edit the entry point (default example is ec2.yaml):



To setup:

Setup authentification
,,,,,,,,,,,,,,,,,,,,,,

Substitute hostname, username and password appropriately and create `~/.buildfarm/jenkins.ini`

```
[jenkins_hostname.example.com]
username=admin
password=changeme
```

Get local code
,,,,,,,,,,,,,,


```
mkdir ros_buildfarm_venv
virtualenv ros_buildfarm_venv
cd ros_buildfarm_venv
. bin/activate
pip install git+git://github.com/dirk-thomas/jenkinsapi.git@feature/config_view
pip install git+git://github.com/ros-infrastructure/rosdistro.git@rep143
git clone https://github.com/ros-infrastructure/ros_buildfarm.git
cd ros_buildfarm
export PYTHONPATH=`pwd`:$PYTHONPATH
```

Run script
,,,,,,,,,,


From inside the venv with the above on your path run the following substituting your config for the one below:

```
./scripts/generate_all_jobs.py https://raw.githubusercontent.example.com/ros-infrastructure/ros_buildfarm_config/master/ec2.yaml
```

Run import_upstream
,,,,,,,,,,,,,,,,,,,

It is important to first log into the machine and run the job `import_upstream` to get all the required bootstrap packages into the repository.
After that you can run the generation jobs which end in `-reconfigure-jobs`
