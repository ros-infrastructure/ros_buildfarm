@[if os_name == 'debian' or os_name == 'ubuntu' and os_code_name in ['saucy', 'vivid', 'wily', 'xenial']]@
@# Ubuntu Saucy, Vivid and newer have neither Python 2 nor 3 installed by default
RUN for i in 1 2 3; do apt update && apt install -q -y python3 && apt clean && break || sleep 5; done
@[end if]@
