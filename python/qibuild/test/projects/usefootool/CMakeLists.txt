## Copyright (c) 2012-2016 Aldebaran Robotics. All rights reserved.
## Use of this source code is governed by a BSD-style license that can be
## found in the COPYING file.
cmake_minimum_required(VERSION 2.8)
project(usefootool)

find_package(qibuild)

find_package(footool REQUIRED)
message(STATUS "FOOTOOL_EXECUTABLE: ${FOOTOOL_EXECUTABLE}")

set(_input ${CMAKE_CURRENT_SOURCE_DIR}/main.in.cpp)
set(_output ${CMAKE_CURRENT_BINARY_DIR}/main.cpp)
qi_generate_src(
  ${_output}
  SRC ${_input}
  COMMAND ${FOOTOOL_EXECUTABLE} ${_input} ${_output}
)

qi_create_bin(usefootool ${_output})
