cmake_minimum_required(VERSION 3.10)

# set the project name
project(catbuffer)

include_directories(${PROJECT_SOURCE_DIR}/../output-symbol/generated_src/ ${PROJECT_SOURCE_DIR}/../output-symbol/static_src/)

link_directories(${PROJECT_SOURCE_DIR}/../output-symbol/_build/)

add_executable(main ${PROJECT_SOURCE_DIR}/src/main.cpp)

target_link_libraries(main PUBLIC catbuffer)
