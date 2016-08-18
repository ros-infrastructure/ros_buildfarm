@[if os_name == 'debian']@
@# Debian does not have locales installed by default but ubuntu does
RUN for i in 1 2 3; do apt-get update && apt-get install -q -y locales && apt-get clean && break || sleep 5; done
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
@[end if]@
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV TZ @timezone
