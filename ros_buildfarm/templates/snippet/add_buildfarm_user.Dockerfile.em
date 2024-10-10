# Add user 'buildfarm', removing any existing user with that UID
RUN if [ $(id -nu @(uid)) ]; then userdel -r $(id -nu @(uid)); fi
RUN useradd -u @(uid) -l -m buildfarm
