@[for install_list in install_lists]@
COPY @(install_list) .
RUN xargs -a @(install_list) python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y -o Debug::pkgProblemResolver=yes
@[end for]@
