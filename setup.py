import sys

from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)


setup(
    name='python-julia',
    version='1.0.0',
    author='Sergei Khoroshilov',
    author_email='kh.sergei@gmail.com',
    packages=['julia'],
    license='The MIT License',
    install_requires=['six'],
    tests_require=['pytest', 'six'],
    cmdclass={'test': PyTest},
    include_package_data=True,
)
