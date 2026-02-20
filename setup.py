from setuptools import setup, find_packages

setup(
  name='cactus_ide',
  version='0.9.2',
  description='Create files that allow modern IDEs to introspect a Cactus installation.',
  long_description='''
  The Cactus Computational Toolkit is the name of the basic infrastructure for the Einstein Toolkit (https://einsteintoolkit.org).
  This repo provides Python scripts that generate files that enable modern IDEs such as VSCode or CLion to understand the header files.
  ''',
  url='http://cct.lsu.edu/~sbrandt/',
  author='Steven R. Brandt',
  author_email='steven@stevenrbrandt.com',
  license='LGPL',
  entry_points = {
    'console_scripts' : [
        'create_compile_commands=cactus_ide.CompileCommands:main',
        'create_cmake=cactus_ide.CactusCmake:main'
    ],
  },
  packages=['cactus_ide'],
  install_requires=['piraha']
)
