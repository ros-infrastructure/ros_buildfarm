# ros_buildfarm

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

# Good practices

These are good practices which will make your life easier, but are not required.
How to do this is not covered in this documentation.

## DNS entries for
It will aid deployment and development to setup proper DNS entries for
the master and repo machines to access them by name instead of address.

# Example deployment

This assumes you have setup

## Buildfarm configuration management

Before launching you will need to have a buildfarm configuration.

### Fork ros_buildfarm_config

Fork [ros_buildfarm_config](https://github.com/ros-infrastructure/ros_buildfarm_config)

Edit it as follows:
 * update the jenkins url `jenkins_url`
 * update the maintainer contact information `notification_emails`(This is important otherwise you may send someone a lot of incorrect emails!)
 * If you are using a custom rosdistro edit `rosdistro_index_url`
 * if you are using a different set of bootstrap packages update the `prerequisites` including `debian_repositories` and `debian_repository_keys`

Edit the entry point (default example is ec2.yaml):

### Notes on forking rosdistro

If you fork the rosdistro and plan to use this buildfarm as the primary for this rosdistro you must edit the rosdistro to point to the cache location on this repository.
This will be under `distributions:ROSDISTRO:distribution_cache` and have it point `REPO_URL/rosdistro_cache/ROSDISTRO-cache.yaml.gz`.

### Bootstrap from workstation

To bootstrap the system you will need to run a script locally which will configure the basic system.
These commands enable you to reconfigure the entire system.

### Setup authentification


Substitute hostname, username and password appropriately and create `~/.buildfarm/jenkins.ini`

```
[jenkins_hostname.example.com]
username=admin
password=changeme
```

### Get local code

Install the following local code

```
mkdir ros_buildfarm_venv
virtualenv --python=python3 ros_buildfarm_venv
cd ros_buildfarm_venv
. bin/activate
pip install git+git://github.com/dirk-thomas/jenkinsapi.git@feature/config_view
pip install git+git://github.com/ros-infrastructure/rosdistro.git@rep143
git clone https://github.com/ros-infrastructure/ros_buildfarm.git
cd ros_buildfarm
export PYTHONPATH=`pwd`:$PYTHONPATH
```

### Run script

From inside the venv with the above on your path run the following substituting your config for the one below:

```
./scripts/generate_all_jobs.py https://raw.githubusercontent.example.com/ros-infrastructure/ros_buildfarm_config/master/ec2.yaml
```


## Instance Administration

Once the buildfarm has been configured as above. There are a few administrative tasks which need to be seen to.

To do these you will need to log in as the admin user through the web interface.


### Run import_upstream

It is important to first log into the machine and run the job `import_upstream` to get all the required bootstrap packages into the repository.

### Run *reconfigure-jobs


After import upstream has completed.
You can run the generation jobs which end in `-reconfigure-jobs`.
This will generate all the individual jobs for packages.



# TODO

This is currently a work in progress. Upcoming features include:

 * Add support for building on top of and extending a rosdistro
  * more on how to fork rosdistro and add custom packages on top (ros/rosdistro)
  * how to keep the fork in sync afterwards
 * extend how to setup clients to use their local repositories
 * how to release custom packages to their farm
 * how to make stable snapshots for testing and release
  * best practices for when to snapshot and release.
