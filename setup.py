#!/usr/bin/env python
# pylint: disable=line-too-long,missing-docstring
# pylint: disable=fixme
'''Setup script for MHTML.'''

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

from distutils import dir_util
from distutils.command.clean import clean as _CleanCommand

import codecs
import os
import re


class CleanCommand(_CleanCommand):
    # see:
    # - https://github.com/dave-shawley/setupext-janitor/blob/master/setupext/janitor.py  # noqa: E501
    # - https://jichu4n.com/posts/how-to-add-custom-build-steps-and-commands-to-setuppy/  # noqa: E501
    user_options = _CleanCommand.user_options[:]
    user_options.extend([
        # The format is (long option, short option, description).
        ('egg-info', None, 'clean up .egg-info dir'),
    ])

    def initialize_options(self):
        super().initialize_options()
        self.egg_info = False

    def finalize_options(self):
        super().finalize_options()

        if self.all:
            self.egg_info = True

    def run(self):
        super().run()

        dir_names = list()

        if self.egg_info:
            for name in os.listdir():
                if name.endswith('.egg-info') and os.path.isdir(name):
                    dir_names.append(name)

        for dir_name in dir_names:
            if os.path.exists(dir_name):
                dir_util.remove_tree(dir_name, dry_run=self.dry_run)
            else:
                self.announce('skipping {0} since it does not exist'
                              .format(dir_name))


def find_version(path):
    '''Find version string in given file.'''
    with codecs.open(path, 'r') as file:
        content = file.read()

    version_match = re.search('''__version__ = ['"]([^'"]+)['"]''',
                              content, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError('Unable to find version string.')


setup(
    # name of module (if it is to be imported)
    name='MHTML',
    version=find_version('mhtml.py'),
    description='MHTML utils for working with chrome/ium blink saved webarchives.',  # noqa: E501
    author='Querela',
    # author_email='',  # TODO
    license='MIT license',
    # license_file='LICENSE',
    url='https://github.com/Querela/MHTML',
    keywords=['MHTML', 'utils', 'web', 'blink'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Utilities',
    ],
    # single python file
    py_modules=['mhtml'],
    packages=[
        'mhtml_scripts',
    ],
    entry_points={
        'console_scripts': [
            'mhtml-extract = mthml_scripts.extract:cli_main',
            'mhtml-extract-main = mhtml_scripts.extract_main:cli_main',
            'mhtml-list = mhtml_scripts.show_infos:cli_main',
        ],
    },
    python_requires='>=3.5',
    # $ pip install -e .
    install_requires=[
    ],
    tests_require=[
    ],
    # $ pip install -e .[dev]
    # $ flake8 *.py
    # $ pylint *.py
    # $ pyment -q "'''" *.py
    extras_require={
        'dev': [
            'flake8',
            'pylint',
            'pyment',
        ]
    },
    # zip_safe=False,
    cmdclass={
        'clean': CleanCommand,
    },
)
