# generated from @template_name

cmake_minimum_required(VERSION 2.8.3)

@[if not build_type_cmake]@
@# catkin needs some special handling to bootstrap
@[if package_name == 'catkin']@
set(catkin_EXTRAS_DIR ${CMAKE_CURRENT_SOURCE_DIR}/cmake)
include(${catkin_EXTRAS_DIR}/all.cmake NO_POLICY_SCOPE)
@[else]@
find_package(catkin REQUIRED)
@[end if]@

# call internal function since project name is unknown
_catkin_package_xml(${CMAKE_CURRENT_BINARY_DIR}/catkin_generated)

if(NOT "${_CATKIN_CURRENT_PACKAGE}" STREQUAL "@package_name")
  message(FATAL_ERROR "The package name does not match")
endif()
@[end if]@# not build_type_cmake

project(@package_name)

@[if not build_type_cmake]@
@[if package_name != 'catkin']@
# select the catkin dependencies from deps
macro(select_catkin_dependencies PREFIX DEPS)
  set(${PREFIX}_DEPENDENCIES "")
  set(${PREFIX}_MESSAGE_DEPENDENCIES "")
  foreach(pkg ${DEPS})
    find_package(${pkg} QUIET)
    if(${${pkg}_FOUND_CATKIN_PROJECT})
      list(APPEND ${PREFIX}_DEPENDENCIES ${pkg})
    endif()
    if(DEFINED CATKIN_DEVEL_PREFIX)
      if(EXISTS ${CATKIN_DEVEL_PREFIX}/share/${pkg}/cmake/${pkg}-msg-paths.cmake)
        list(APPEND ${PREFIX}_MESSAGE_DEPENDENCIES ${pkg})
      endif()
    endif()
    foreach(workspace ${CATKIN_WORKSPACES})
      if(EXISTS ${workspace}/share/${pkg}/cmake/${pkg}-msg-paths.cmake)
        list(APPEND ${PREFIX}_MESSAGE_DEPENDENCIES ${pkg})
      endif()
    endforeach()
  endforeach()

  message(${PROJECT_NAME} " has " ${PREFIX} " message dependencies:")
  foreach(pkg ${${PREFIX}_MESSAGE_DEPENDENCIES})
    message("  - ${pkg}")
  endforeach()
  message(${PROJECT_NAME} " has " ${PREFIX} " dependencies:")
  foreach(pkg ${${PREFIX}_DEPENDENCIES})
    message("  - ${pkg}")
  endforeach()
endmacro()


# call find_package on build dependencies
if(DEFINED ${PROJECT_NAME}_BUILD_DEPENDS)
  select_catkin_dependencies(BUILD "${${PROJECT_NAME}_BUILD_DEPENDS}")
  find_package(catkin REQUIRED COMPONENTS ${BUILD_DEPENDENCIES})
endif()

# restore variable set by _catkin_package_xml()
# since they might have been overridden by now
include(${CMAKE_CURRENT_BINARY_DIR}/catkin_generated/package.cmake)

# use setup.py when available
if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/setup.py")
  catkin_python_setup()
endif()

if(genmsg_FOUND)
  # generate messages
  file(GLOB message_files RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}/msg" msg/*.msg)
  list(LENGTH message_files message_count)
  if(${message_count} GREATER 0)
    add_message_files(DIRECTORY msg FILES ${message_files})
  endif()

  # generate services
  file(GLOB service_files RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}/srv" srv/*.srv)
  list(LENGTH service_files service_count)
  if(${service_count} GREATER 0)
    add_service_files(DIRECTORY srv FILES ${service_files})
  endif()

  if(actionlib_msgs_FOUND)
    # generate actions
    file(GLOB action_files RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}/action" action/*.action)
    list(LENGTH action_files action_count)
    if(${action_count} GREATER 0)
      add_action_files(DIRECTORY action FILES ${action_files})
    endif()
  else()
    set(action_count 0)
  endif()

  # invoke message generation
  if(${message_count} GREATER 0 OR ${service_count} GREATER 0 OR ${action_count} GREATER 0)
    generate_messages(DEPENDENCIES ${BUILD_MESSAGE_DEPENDENCIES})
  endif()
endif()

# call catkin_package() with run dependencies
if(DEFINED ${PROJECT_NAME}_RUN_DEPENDS)
  select_catkin_dependencies(RUN "${${PROJECT_NAME}_RUN_DEPENDS}")
endif()
@[end if]@# package_name != 'catkin'

@# don't install CMake config file for actionlib_msgs
@# allow to use the installed underlay binary package
@[if package_name != 'actionlib_msgs']@
catkin_package(
  DEPENDS ${RUN_DEPENDENCIES}
)
@[end if]@

@[else]@
install(FILES package.xml DESTINATION share/${PROJECT_NAME})
@[end if]@# not build_type_cmake
