# Cactus IDE
## To install:

    pip install git+https://github.com/stevenrbrandt/cactus_ide.git

## To use with VSCode:
    
    create_compile_commands --cactus-root ~/Cactus --config sim

The result of this command will be a compile-commands.json file in the
Cactus root directory.

## To use with CLion

    create_cmake --cactus-root ~/Cactus --config sim

The result of this command will be a CMakeLists.txt file in the
Cactus root directory, along with include files for each thorn
in the configs directory.

This CMakeLists.txt cannot yet be used to build Cactus, but it will
help CLion in following include files and defining symbols.
