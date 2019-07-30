import os
from setuptools import setup, find_packages

import solo

README = os.path.join(os.path.dirname(__file__), 'README.rst')

# When running tests using tox, README.md is not found
try:
    with open(README) as file:
        long_description = file.read()
except Exception:
    long_description = ''

setup(
    name='django-solo',
    version=solo.__version__,
    description=solo.__doc__,
    packages=find_packages(),
    url='http://github.com/lazybird/django-solo/',
    author='lazybird',
    long_description=long_description,
    include_package_data=True,
    license='Creative Commons Attribution 3.0 Unported',
)
