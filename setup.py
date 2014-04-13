from setuptools import setup

setup(
    name='python-julia',
    version='1.0.0',
    author='Sergei Khoroshilov',
    author_email='kh.sergei@gmail.com',
    packages=['julia'],
    license='The MIT License',
    install_requires=['six'],
    include_package_data=True,
)