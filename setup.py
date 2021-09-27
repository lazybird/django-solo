from setuptools import setup, find_packages
import os
import solo


README = os.path.join(os.path.dirname(__file__), 'README.md')

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
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    include_package_data=True,
    zip_safe=False,
    license='Creative Commons Attribution 3.0 Unported',
)
