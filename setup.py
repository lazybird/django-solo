from setuptools import setup, find_packages

import solo


setup(
    name='django-solo',
    version=solo.__version__,
    description=solo.__doc__,
    packages=find_packages(),
    url='http://github.com/lazybird/django-solo/',
    author='lazybird',
    long_description=open('README.md').read(),
    include_package_data=True,
    license='Creative Commons Attribution 3.0 Unported',
)
