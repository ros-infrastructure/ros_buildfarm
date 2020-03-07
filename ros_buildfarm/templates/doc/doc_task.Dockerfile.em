# generated from @template_name

@(TEMPLATE(
    'snippet/from_base_image.Dockerfile.em',
    os_name=os_name,
    os_code_name=os_code_name,
    arch=arch,
))@

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive

@(TEMPLATE(
    'snippet/old_release_set.Dockerfile.em',
    os_name=os_name,
    os_code_name=os_code_name,
))@

@(TEMPLATE(
    'snippet/setup_locale.Dockerfile.em',
    timezone=timezone,
))@

RUN useradd -u @uid -l -m buildfarm

@(TEMPLATE(
    'snippet/set_environment_variables.Dockerfile.em',
    environment_variables=environment_variables,
))@

@(TEMPLATE(
    'snippet/add_distribution_repositories.Dockerfile.em',
    distribution_repository_keys=distribution_repository_keys,
    distribution_repository_urls=distribution_repository_urls,
    os_name=os_name,
    os_code_name=os_code_name,
    add_source=False,
))@

@(TEMPLATE(
    'snippet/add_additional_repositories.Dockerfile.em',
    os_name=os_name,
    os_code_name=os_code_name,
    arch=arch,
))@

@(TEMPLATE(
    'snippet/add_wrapper_scripts.Dockerfile.em',
    wrapper_scripts=wrapper_scripts,
))@

# automatic invalidation once every day
RUN echo "@today_str"

@(TEMPLATE(
    'snippet/install_python3.Dockerfile.em',
    os_name=os_name,
    os_code_name=os_code_name,
))@

@[if build_tool == 'colcon']@
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y python3-pip
@# colcon-core.package_identification.python needs at least version 30.3.0
RUN pip3 install -U setuptools
@[end if]@

@(TEMPLATE(
    'snippet/install_dependencies.Dockerfile.em',
    dependencies=dependencies,
    dependency_versions=dependency_versions,
))@

@(TEMPLATE(
    'snippet/install_dependencies_from_file.Dockerfile.em',
    install_lists=install_lists,
))@

@[if os_name == 'ubuntu' and os_code_name[0] == 't']@
# Doxygen version 1.8.6 seems to generate excessive tagfiles when cross referencing,
# overriding with older package (1.7.6) from Precise
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y wget
RUN rm /usr/bin/doxygen
RUN wget --no-verbose http://us.archive.ubuntu.com/ubuntu/pool/main/d/doxygen/doxygen_1.7.6.1-2ubuntu1_amd64.deb --output-document=/tmp/doxygen_1.7.6.1-2ubuntu1_amd64.deb
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
    ' --build-tool ' + build_tool + \
    ' --workspace-root /tmp/ws' + \
    ' --rosdoc-lite-dir /tmp/rosdoc_lite' + \
    ' --catkin-sphinx-dir /tmp/catkin-sphinx' + \
    ' --rosdoc-index /tmp/rosdoc_index' + \
    (' --canonical-base-url ' + canonical_base_url if canonical_base_url else '') + \
    ' --output-dir /tmp/generated_documentation' + \
    ' ' + ' '.join(pkg_tuples)
}@
CMD ["@cmd"]
