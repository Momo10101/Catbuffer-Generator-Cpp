cmake_minimum_required(VERSION 3.10)

project(catbuffer)
set (CMAKE_CXX_STANDARD 11)

set (CMAKE_CXX_FLAGS "-Wall -Werror -Wextra -Winit-self -Woverloaded-virtual -Wuninitialized -Winit-self -ansi -pedantic -pedantic-errors ")

include_directories(${PROJECT_SOURCE_DIR}/static_src)

file(GLOB GEN_SRC_FILES ${PROJECT_SOURCE_DIR}/generated_src/*.cpp)
file(GLOB STATIC_SRC_FILES ${PROJECT_SOURCE_DIR}/static_src/*.cpp)

add_library(catbuffer ${GEN_SRC_FILES} ${STATIC_SRC_FILES})


