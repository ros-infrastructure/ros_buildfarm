@[if os_name == 'ubuntu']@
@[  if arch in ['amd64', 'i386']]@
# Add multiverse
RUN echo "deb http://archive.ubuntu.com/ubuntu/ @(os_code_name) multiverse" >> /etc/apt/sources.list && echo "deb-src http://archive.ubuntu.com/ubuntu/ @(os_code_name) multiverse" >> /etc/apt/sources.list && echo "deb-src http://archive.ubuntu.com/ubuntu/ @(os_code_name)-updates multiverse" >> /etc/apt/sources.list && echo "deb-src http://archive.ubuntu.com/ubuntu/ @(os_code_name)-updates multiverse" >> /etc/apt/sources.list && echo "deb-src http://archive.ubuntu.com/ubuntu/ @(os_code_name)-security multiverse" >> /etc/apt/sources.list && echo "deb-src http://archive.ubuntu.com/ubuntu/ @(os_code_name)-security multiverse" >> /etc/apt/sources.list
@[  elif arch in ['armhf', 'armv8']]@
# Add multiverse
RUN echo "deb http://ports.ubuntu.com/ @(os_code_name) multiverse" >> /etc/apt/sources.list && echo "deb-src http://ports.ubuntu.com/ @(os_code_name) multiverse" >> /etc/apt/sources.list && echo "deb-src http://ports.ubuntu.com/ @(os_code_name)-updates multiverse" >> /etc/apt/sources.list && echo "deb-src http://ports.ubuntu.com/ @(os_code_name)-updates multiverse" >> /etc/apt/sources.list && echo "deb-src http://ports.ubuntu.com/ @(os_code_name)-security multiverse" >> /etc/apt/sources.list && echo "deb-src http://ports.ubuntu.com/ @(os_code_name)-security multiverse" >> /etc/apt/sources.list
@[  end if]@
@[else if os_name == 'debian']@
# Add contrib and non-free to debian images
RUN echo deb http://http.debian.net/debian @os_code_name contrib non-free | tee -a /etc/apt/sources.list
@[end if]@
