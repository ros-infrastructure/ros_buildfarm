FROM @os_name:@os_code_name
MAINTAINER @maintainer_name @maintainer_email

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive

RUN mkdir /tmp/keys
@[for i, key in enumerate(distribution_repository_keys)]@
RUN echo "@('\\n'.join(key.splitlines()))" > /tmp/keys/@(i).key
RUN apt-key add /tmp/keys/@(i).key
@[end for]@
@[for url in distribution_repository_urls]@
RUN echo deb @url @os_code_name main | tee /etc/apt/sources.list.d/buildfarm.list
@[end for]@

RUN apt-get update
RUN apt-get install -q -y python3-apt python3-catkin-pkg python3-empy python3-rosdep

RUN useradd -u @uid -m buildfarm
RUN rosdep init
RUN su buildfarm -c "rosdep --rosdistro=@rosdistro_name update"

CMD ["su", "buildfarm", "-c", "PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u /tmp/ros_buildfarm/scripts/devel/create_devel_task_generator.py --rosdistro-name @rosdistro_name --workspace-root /tmp/catkin_workspace --os-name @os_name --os-code-name @os_code_name --distribution-repository-urls @(' '.join(distribution_repository_urls)) --distribution-repository-key-files @(' ' .join(['/tmp/keys/%d.key' % i for i in range(len(distribution_repository_keys))])) --dockerfile-dir /tmp/docker_build_and_install && PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u /tmp/ros_buildfarm/scripts/devel/create_devel_task_generator.py --rosdistro-name @rosdistro_name --workspace-root /tmp/catkin_workspace --os-name @os_name --os-code-name @os_code_name --distribution-repository-urls @(' '.join(distribution_repository_urls)) --distribution-repository-key-files @(' ' .join(['/tmp/keys/%d.key' % i for i in range(len(distribution_repository_keys))])) --testing --dockerfile-dir /tmp/docker_build_and_test"]
