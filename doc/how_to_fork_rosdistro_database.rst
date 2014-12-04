How to fork the rosdistro database?
===================================

Instead of using the official rosdistro database you can fork the repository to
maintain a custom state.
This enables you to decide when changes from the official database are being
merged in order to:

* achieve a more conservative release strategy

* lock the version number of specific repositories / packages

After the initial for it is your responsibility to keep the fork in sync if you
want to.


Update reference to custom cache
--------------------------------

The rosdistro repository contains references to the rosdistro cache files.

After forking the repository you must update the URLs to your custom
locations for each distribution::

    index.yaml:
      distributions:
        ROS_DISTRO_NAME:
          distribution_cache: http://repo_hostname.example.com/rosdistro_cache/ROS_DISTRO_NAME-cache.yaml.gz


Update buildfarm configuration
------------------------------

Edit your buildfarm configuration file to point to the forked rosdistro
``index.yaml`` file::

    rosdistro_index_url: https://raw.github.com/YOUR_FORK/rosdistro/master/index.yaml

After changing the configuration of an existing buildfarm you have to
reconfigure *all* jobs and should make sure that the rosdistro cache file is
generated correctly.


Users must explicitly use the forked database
---------------------------------------------

Every user must set an environment variable on his machine to use the modified
rosdistro::

    ROSDISTRO_INDEX_URL=https://raw.github.com/YOUR_FORK/rosdistro/master/index.yaml

After that you must update the rosdep database to use the ROS packages from
your forked repository::

    rosdep update


Use the forked rosdep database or keep using the official one?
--------------------------------------------------------------

With the fork of the rosdistro repository you also have a custom set of rosdep
files.
By default rosdep keeps using the database from the official repository.

If you want to maintain and use your custom version of the rosdep database
included in the forked rosdistro repository you have to perform the following
changes:

* Update all URLs in the rosdep list file
  ``rosdep/sources.list.d/20-default.list`` to point to you custom fork.

* Update any of the ``.yaml`` files as you like

After that every user must perform the following tasks to use your forked
rosdep database:

* Remove the existing rosdep list files::

    sudo rm /etc/ros/rosdep/sources.list.d/20-default.list

* Download the custom rosdep list file::

    cd /etc/ros/rosdep/sources.list.d
    sudo wget https://raw.github.com/YOUR_FORK/rosdistro/master/rosdep/sources.list.d/20-default.list

* Update the local rosdep database::

    rosdep update

rosdep always uses the ROS packages defined by the ROSDISTRO_INDEX_URL variable
when updating the rosdep database.
