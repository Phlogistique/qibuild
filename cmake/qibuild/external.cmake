## Copyright (C) 2011 Aldebaran Robotics

cmake_minimum_required(VERSION 2.8.3)
include(ExternalProject)


#! qiBuild External
# =================

#!
# This modules allow building external projects.
# Install rules for these projects are autogenerated.

#! Compile an autotools based project
# \arg:name The name of the project
# \arg:url The url of the project to download. (could start with http:// or file://)
# \param:MD5 The md5 of the specified file
# \group:PATCH A list of patches to apply before building
# \group:CONFIGURE_OPTIONS Optional configure options
# \group:INSTALL_OPTIONS Arguments to pass to the install command
function(qi_build_autotools name url)
  cmake_parse_arguments(ARGS "" "MD5" "PATCH;INSTALL_OPTIONS;CONFIGURE_OPTIONS" ${ARGN})

  set(options)
  list(APPEND options "${ARGS_CONFIGURE_OPTIONS}")

  set(patchs_cmd)
  foreach(p ${ARGS_PATCH})
    list(APPEND patchs_cmd "patch" "-p1" "<" "${p}" ";")
  endforeach()

  ExternalProject_Add(${name}
    URL               "${url}"
    URL_MD5           "${ARGS_MD5}"
    PREFIX            "${name}"
    BUILD_IN_SOURCE   1
    PATCH_COMMAND     "${patchs_cmd}"
    CONFIGURE_COMMAND "./configure" --prefix=/. ${options}
    INSTALL_COMMAND   "DESTDIR=${QI_SDK_DIR}" make install ${ARGS_INSTALL_OPTIONS}
    )

  #generate install rules for the project
  qi_install_external_project()
endfunction()


#! Compiles a CMake based project
# \arg:name The name of the project
# \arg:url The url of the project to download. (could start with http:// or file://)
# \param:MD5 The md5 of the specified file
# \group:PATCH A list of patches to apply before building
# \group:CMAKE_FLAGS Optional cmake flags
function(qi_build_cmake name url)
  cmake_parse_arguments(ARGS "" "MD5" "PATCH;CMAKE_ARGS" ${ARGN})

  set(patchs_cmd)
  foreach(p ${ARGS_PATCH})
    list(APPEND patchs_cmd "patch" "-p1" "<" "${p}" ";")
  endforeach()

  #/ is not a valid install_prefix in most place
  #so we use /sdk and set DESTDIR to ..
  set(_cmake_args "-DCMAKE_INSTALL_PREFIX=/sdk" ${ARGS_CMAKE_ARGS})

  ExternalProject_Add(${name}
  URL "${url}"
  URL_MD5 "${ARGS_MD5}"
  PREFIX "${name}"
  BUILD_IN_SOURCE 0
  PATCH_COMMAND "${patchs_cmd}"
  CMAKE_ARGS ${_cmake_args}
  INSTALL_COMMAND   "DESTDIR=${QI_SDK_DIR}/../" make install ${ARGS_INSTALL_OPTIONS}
  )

  #generate install rules for the project
  qi_install_external_project()
endfunction()

function(qi_install_external_project)
  install(DIRECTORY "${QI_SDK_DIR}" DESTINATION "${CMAKE_INSTALL_PREFIX}")
  # FIXME: on mac, do something with install_name ?
endfunction()
