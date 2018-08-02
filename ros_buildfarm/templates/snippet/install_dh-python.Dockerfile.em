@[if (os_name == 'ubuntu' and os_code_name not in ['trusty', 'xenial', 'artful']) or (os_name == 'debian' and os_code_name not in ['jessie', 'stretch'])]@
@# Ubuntu Bionic doesn't ship dh-python with python3 anymore
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y dh-python
@[end if]@
