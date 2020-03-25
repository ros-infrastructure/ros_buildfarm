@[for install_list in install_lists]@
COPY @(install_list) .
RUN sed '/^#.*/d' @(install_list) | xargs python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y -o Debug::pkgProblemResolver=yes
@[end for]@
