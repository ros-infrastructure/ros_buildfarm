RUN mkdir /tmp/keys
@[if os_name == 'debian' and os_code_name == 'stretch']@
@# In Debian Stretch apt doesn't depend on gnupg anymore
@# https://anonscm.debian.org/cgit/apt/apt.git/commit/?id=87d468fe355c87325c943c40043a0bb236b2407f
RUN for i in 1 2 3; do apt-get update && apt-get install -q -y gnupg && apt-get clean && break || if [[ $i < 3 ]]; then sleep 5; else false; fi; done
@[end if]@
@[for i, key in enumerate(distribution_repository_keys)]@
RUN echo "@('\\n'.join(key.splitlines()))" > /tmp/keys/@(i).key && apt-key add /tmp/keys/@(i).key
@[end for]@
@[for url in distribution_repository_urls]@
RUN echo deb @url @os_code_name main | tee -a /etc/apt/sources.list.d/buildfarm.list
@[if add_source and url == target_repository]@
RUN echo deb-src @url @os_code_name main | tee -a /etc/apt/sources.list.d/buildfarm.list
@[end if]@
@[end for]@
@[if os_name == 'ubuntu']@
# Enable multiverse
RUN sed -i "/^# deb.*multiverse/ s/^# //" /etc/apt/sources.list
@[else if os_name == 'debian']@
# Add contrib and non-free to debian images
RUN echo deb http://http.debian.net/debian @os_code_name contrib non-free | tee -a /etc/apt/sources.list
@[end if]@
