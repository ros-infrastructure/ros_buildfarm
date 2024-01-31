@[if os_name == 'debian' or os_name == 'ubuntu']@
@# python3-pytest-rerunfailures is supported since Ubuntu jammy
RUN for i in 1 2 3; do apt-get update && apt-get install -q -y python3-pytest-rerunfailures && apt-get clean && break || if [ $i -lt 3 ]; then sleep 5; else false; fi; done
@[end if]@
