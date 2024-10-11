# Opt-out of phased updates, which can create inconsistencies between installed package versions as different containers end up on different phases.
# https://wiki.ubuntu.com/PhasedUpdates
RUN echo 'APT::Get::Never-Include-Phased-Updates "true";' > /etc/apt/apt.conf.d/90-phased-updates
