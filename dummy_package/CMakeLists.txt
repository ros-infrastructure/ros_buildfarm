cmake_minimum_required(VERSION 2.8.3)
project(dummy_package)

find_package(catkin REQUIRED)

message("Dummy package with nothing inside")

catkin_package()
