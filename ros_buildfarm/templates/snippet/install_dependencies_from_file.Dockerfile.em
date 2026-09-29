@{
pkg_format = package_format_mapping.get(vars().get('os_name'), 'deb') if vars().get('os_name') else 'deb'
wrapper_script = 'apt.py' if pkg_format == 'deb' else 'dnf.py'
extra_flags = ' -o Debug::pkgProblemResolver=yes' if pkg_format == 'deb' else ''
}@
@[for install_list in install_lists]@
COPY @(install_list) .
RUN sed '/^#.*/d' @(install_list) | xargs python3 -u /tmp/wrapper_scripts/@(wrapper_script) update-install-clean -q -y@(extra_flags)
@[end for]@
