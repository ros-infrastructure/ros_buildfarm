# generated from @template_name

@(TEMPLATE(
    'snippet/from_base_image.Dockerfile.em',
    os_name=os_name,
    os_code_name=os_code_name,
    arch=arch,
))@
MAINTAINER Dirk Thomas dthomas+buildfarm@@osrfoundation.org

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8

RUN useradd -u @uid -m buildfarm

@(TEMPLATE(
    'snippet/add_distribution_repositories.Dockerfile.em',
    distribution_repository_keys=distribution_repository_keys,
    distribution_repository_urls=distribution_repository_urls,
    os_code_name=os_code_name,
    add_source=False,
))@

@[if os_name == 'ubuntu']@
# Add multiverse
RUN echo deb http://archive.ubuntu.com/ubuntu @os_code_name multiverse | tee -a /etc/apt/sources.list
@[else if os_name == 'debian']@
# Add contrib and non-free to debian images
RUN echo deb http://http.debian.net/debian @os_code_name contrib non-free | tee -a /etc/apt/sources.list
@[end if]@

@(TEMPLATE(
    'snippet/add_wrapper_scripts.Dockerfile.em',
    wrapper_scripts=wrapper_scripts,
))@

# automatic invalidation once every day
RUN echo "@today_str"

@# Ubuntu before Trusty explicitly needs python3
@[if os_name == 'ubuntu' and os_code_name[0] < 't']@
RUN python -u /tmp/wrapper_scripts/apt-get.py update-and-install -q -y python3
@[end if]@

@(TEMPLATE(
    'snippet/install_dependencies.Dockerfile.em',
    dependencies=dependencies,
    dependency_versions=dependency_versions,
))@

@[if os_name == 'ubuntu' and os_code_name[0] == 't']@
# Doxygen version 1.8.6 seems to generate excessive tagfiles when cross referencing,
# overriding with older package (1.7.6) from Precise
RUN python3 -u /tmp/wrapper_scripts/apt-get.py update-and-install -q -y wget
RUN rm /usr/bin/doxygen
RUN wget http://us.archive.ubuntu.com/ubuntu/pool/main/d/doxygen/doxygen_1.7.6.1-2ubuntu1_amd64.deb --output-document=/tmp/doxygen_1.7.6.1-2ubuntu1_amd64.deb
RUN dpkg -i /tmp/doxygen_1.7.6.1-2ubuntu1_amd64.deb
RUN doxygen --version
@[end if]@

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
# empy fails using rosdoc_config_files in a list comprehension
pkg_tuples = []
for pkg_path, pkg in ordered_pkg_tuples:
    pkg_tuples.append('%s:%s:%s' % (pkg.name, pkg_path, rosdoc_config_files.get(pkg.name, '')))
cmd = 'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/doc/build_doc.py' + \
    ' --rosdistro-name ' + rosdistro_name + \
    ' --os-code-name ' + os_code_name + \
    ' --arch ' + arch + \
    ' --workspace-root /tmp/catkin_workspace' + \
    ' --rosdoc-lite-dir /tmp/rosdoc_lite' + \
    ' --catkin-sphinx-dir /tmp/catkin-sphinx' + \
    ' --rosdoc-index /tmp/rosdoc_index' + \
    (' --canonical-base-url ' + canonical_base_url if canonical_base_url else '') + \
    ' --output-dir /tmp/generated_documentation' + \
    ' ' + ' '.join(pkg_tuples)
}@
CMD ["@cmd"]
