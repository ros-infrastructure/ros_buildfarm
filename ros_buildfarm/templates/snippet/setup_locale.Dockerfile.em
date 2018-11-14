RUN for i in 1 2 3; do apt-get update && apt-get install -q -y locales && apt-get clean && break || if [ $i -lt 3 ]; then sleep 5; else false; fi; done
RUN echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV TZ @timezone
