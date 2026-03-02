# Cactus IDE

This utility is designed to make it easier to work on the [Einstein Toolkit](https://einsteintoolkit.org).

The ET has a unique/non-standard way of generating headers and building, making it difficult for ET programmers to benefit from IDEs. This utility helps by creating either a compile_commands.json or a CMakeLists.txt file that will help the editors navigate headers and identify symbols.

## To install:

    pip install git+https://github.com/stevenrbrandt/cactus_ide.git

## To use with VSCode or vim (for vim setup, see below):
    
    create_compile_commands --cactus-root ~/Cactus --config sim

The result of this command will be a compile_commands.json file in the
Cactus root directory.

## To use with CLion

    create_cmake --cactus-root ~/Cactus --config sim

The result of this command will be a CMakeLists.txt file in the
Cactus root directory, along with include files for each thorn
in the configs directory.

This CMakeLists.txt cannot yet be used to build Cactus, but it will
help CLion in following include files and defining symbols.

## To use with vim

Step zero: Generate the compile_commands.json file

Step one: Make sure you have the following installed:

    # On Ubuntu/Debian
    apt install -y nodejs npm clangd

If you do not have root, you can install the prerequisites like this:

    # if clangd isn't available on your system, you can install it like this:
    git clone --depth 1 https://github.com/llvm/llvm-project.git
    cd llvm-project/
    cmake -S llvm -B build -DLLVM_ENABLE_ZSTD=OFF -DLLVM_ENABLE_PROJECTS='clang;clang-tools-extra' -DCMAKE_INSTALL_PREFIX=/project/sbrandt/llvm-install -DCMAKE_BUILD_TYPE=Release
    make -j8 install

    # You'll need nvm/node. If it's not available, you can install it like this:
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.5/install.sh | bash
    nvm install --lts
    nvm install node

Note that clangd should be in your path. If it's not, you should set your ~/.vim/coc-settings.json like this:

    {
      "clangd.path": "/project/sbrandt/llvm-install/bin/clangd"
    }

Step two: Add the following to your ~/.vimrc

    call plug#begin()
    Plug 'neoclide/coc.nvim', {'branch': 'release'}
    call plug#end()
    " Go to definition
    nmap <silent> gd <Plug>(coc-definition)
    " Go to type definition (useful for classes/templates)
    nmap <silent> gy <Plug>(coc-type-definition)
    " Go to implementation
    nmap <silent> gi <Plug>(coc-implementation)
    " Find references
    nmap <silent> gr <Plug>(coc-references)

Step 3: Run this command to enable plugins:

    curl -fLo ~/.vim/autoload/plug.vim --create-dirs \
        https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim

Step 4: When you start up vim, run the following two commands:

    :PlugInstall
    :CocInstall coc-clangd

You are now good to go! You can type "gd" to go to a definition and Ctrl-o to return.
