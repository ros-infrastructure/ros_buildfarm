@[if os_name == 'debian' or os_name == 'ubuntu' and os_code_name not in ['trusty', 'utopic']]@
@# Ubuntu Saucy, Vivid and newer have neither Python 2 nor 3 installed by default
RUN for i in 1 2 3; do apt-get update && apt-get install -q -y python3 && apt-get clean && break || if [ $i -lt 3 ]; then sleep 5; else false; fi; done
@[end if]@
