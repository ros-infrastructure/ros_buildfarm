@[if os_name == 'ubuntu' and os_code_name not in ['trusty', 'xenial', 'artful']]@
@# Ubuntu Bionic doesn't ship dh-python with python3 anymore
RUN for i in 1 2 3; do apt-get update && apt-get install -q -y dh-python && apt-get clean && break || if [[ $i < 3 ]]; then sleep 5; else false; fi; done
@[end if]@
