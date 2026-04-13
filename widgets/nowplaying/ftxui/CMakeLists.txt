cmake_minimum_required(VERSION 3.14)
project(nowplaying CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_BUILD_TYPE Release)

include(FetchContent)
FetchContent_Declare(
    ftxui
    GIT_REPOSITORY https://github.com/ArthurSonzogni/FTXUI
    GIT_TAG        v5.0.0
    GIT_SHALLOW    TRUE
)
FetchContent_MakeAvailable(ftxui)

add_executable(nowplaying main.cpp)
target_link_libraries(nowplaying PRIVATE
    ftxui::component
    ftxui::dom
    ftxui::screen
)
