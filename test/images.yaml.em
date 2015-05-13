%YAML 1.1
# ROS Dockerfile database
---
images:
    ros_core:
        base_image: @(os_name):@(os_code_name)
        template_name: docker_images/test.Dockerfile.em
        template_packages:
            - ros_foo
        packages:
            - wget
        ros_packages:
            - ros-core
