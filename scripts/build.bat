@echo off

set "BUILD_TYPE=%1" 
set "CXX_STANDARD=20"
set "CUDA_STANDARD=20"
set "BUILD_SHARED_LIBS=OFF"
set "BUILD_CUDA_EXAMPLES=OFF"

call cmake -G Ninja -S . -B ./build  ^
    -DCMAKE_BUILD_TYPE=%BUILD_TYPE%   ^
    -DCMAKE_CXX_STANDARD=%CXX_STANDARD%  ^
    -DCMAKE_CUDA_STANDARD=%CUDA_STANDARD%  ^
    -DBUILD_CUDA_EXAMPLES=%BUILD_CUDA_EXAMPLES%  ^
    -DBUILD_SHARED_LIBS=%BUILD_SHARED_LIBS%

set "NUMBER_OF_PROCESSORS=8"

call cmake --build ./build -j %NUMBER_OF_PROCESSORS%

call cmake --install ./build --prefix ./build/install
