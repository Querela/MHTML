#!/usr/bin/env python
# pylint: disable=line-too-long,missing-docstring
# pylint: disable=attribute-defined-outside-init
# pylint: disable=fixme
'''Setup script for MHTML.'''

try:
    from setuptools import setup, Command
except ImportError:
    from distutils.core import setup, Command

import distutils.log
from distutils import dir_util
from distutils.command.clean import clean as _CleanCommand  # noqa: N812

import codecs
import os
import re
import subprocess


class CleanCommand(_CleanCommand):
    # see:
    # - https://github.com/dave-shawley/setupext-janitor/blob/master/setupext/janitor.py  # noqa: E501
    # - https://jichu4n.com/posts/how-to-add-custom-build-steps-and-commands-to-setuppy/  # noqa: E501
    user_options = _CleanCommand.user_options[:]
    user_options.extend([
        # The format is (long option, short option, description).
        ('egg-base=', 'e',
         'directory containing .egg-info directories '
         '(default: top of the source tree)'),
        ('eggs', None, 'remove *.egg-info and *.eggs directories'),
        ('pycache', 'p', 'remove __pycache__ directories'),
    ])
    boolean_options = _CleanCommand.boolean_options[:]
    boolean_options.extend(['eggs', 'pycache'])

    def initialize_options(self):
        super().initialize_options()
        self.egg_base = None
        self.eggs = False
        self.pycache = False

    def finalize_options(self):
        super().finalize_options()

        if self.egg_base is None:
            self.egg_base = os.curdir

        if self.all:
            self.eggs = True
            self.pycache = True

    def run(self):
        super().run()

        dir_names = set()

        if self.eggs:
            for name in os.listdir(self.egg_base):
                dname = os.path.join(self.egg_base, name)
                if name.endswith('.egg-info') and os.path.isdir(dname):
                    dir_names.add(dname)
            for name in os.listdir(os.curdir):
                if name.endswith('.egg'):
                    dir_names.add(name)
                if name == '.eggs':
                    dir_names.add(name)

        if self.pycache:
            for root, dirs, _ in os.walk(os.curdir):
                if '__pycache__' in dirs:
                    dir_names.add(os.path.join(root, '__pycache__'))

        for dir_name in dir_names:
            if os.path.exists(dir_name):
                dir_util.remove_tree(dir_name, dry_run=self.dry_run)
            else:
                self.announce('skipping {0} since it does not exist'
                              .format(dir_name))


class PylintCommand(Command):
    '''A custom command to run Pylint on all Python source files.
    see: https://jichu4n.com/posts/how-to-add-custom-build-steps-and-commands-to-setuppy/
    '''  # noqa: E501

    description = 'run Pylint on Python source files'
    user_options = [
        ('no-color', None, 'suppress auto coloring'),
        ('pylint-rcfile=', None, 'path to Pylint config file'),
        ('dir=', None, 'path to run Pylint on'),
    ]

    boolean_options = ['no-color']

    def initialize_options(self):
        '''Set default values for options.'''
        self.pylint_rcfile = ''
        self.no_color = False
        self.dir = ''

    def finalize_options(self):
        '''Post-process options.'''
        if self.pylint_rcfile:
            assert os.path.exists(self.pylint_rcfile), \
                ('Pylint config file %s does not exist.' % self.pylint_rcfile)
        if self.dir:
            assert os.path.exists(self.dir), \
                    ('Folder %s to check does not exist.' % self.dir)

    def package_files(self, no_recurse_list=False):
        '''Collect the files/dirs included in the registered modules.'''
        seen_package_directories = ()
        directories = self.distribution.package_dir or {}
        empty_directory_exists = '' in directories
        packages = self.distribution.packages or []
        for package in packages:
            package_directory = package
            if package in directories:
                package_directory = directories[package]
            elif empty_directory_exists:
                package_directory = os.path.join(
                    directories[''], package_directory
                )

            if not no_recurse_list and \
                    package_directory.startswith(seen_package_directories):
                continue

            seen_package_directories += (package_directory + '.',)
            yield package_directory

    def module_files(self):
        '''Collect the files listed as py_modules.'''
        modules = self.distribution.py_modules or []
        filename_from = '{0}.py'.format
        for module in modules:
            yield filename_from(module)

    def distribution_files(self):
        '''Collect package and module files.
        From: https://gitlab.com/pycqa/flake8/blob/master/src/flake8/main/setuptools_command.py
        '''  # noqa: E501
        for package in self.package_files():
            yield package

        for module in self.module_files():
            yield module

        yield 'setup.py'

    def run(self):
        '''Run command.'''
        command = ['pylint']
        # command.append('-d F0010')  # TODO: hmmm?
        if not self.no_color:
            command.append('--output-format=colorized')
        if self.pylint_rcfile:
            command.append('--rcfile=%s' % self.pylint_rcfile)
        if self.dir:
            command.append(self.dir)
        else:
            # command.append(os.getcwd())
            for name in self.distribution_files():
                command.append(name)
            # command.append('*.py')
            # command.append('**/*.py')

        self.announce(
            'Running command: %s' % str(command), level=distutils.log.INFO)
        try:
            subprocess.check_call(' '.join(command), shell=True)
        except subprocess.CalledProcessError as cpe:
            self.announce(cpe, level=distutils.log.ERROR)
            # see: flake8 handling
            raise SystemExit from cpe
        # self.spawn(command)


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
            'mhtml-headers = mhtml_scripts.show_headers:cli_main',
        ],
    },
    python_requires='>=3.5',
    # $ pip install -e .
    install_requires=[
    ],
    tests_require=[
        'pytest',
        'pytest-cov',
        'pytest-pylint',
    ],
    # $ pip install -e .[dev]
    # $ flake8 *.py
    # $ pylint *.py
    # $ pyment -q "'''" *.py
    # $ prospector
    extras_require={
        'dev': [
            'flake8',
            'pylint',
            'pyment',
        ]
    },
    setup_requires=[
        'pytest-runner',
    ],
    # zip_safe=False,
    cmdclass={
        'clean': CleanCommand,
        'pylint': PylintCommand,
    },
)
