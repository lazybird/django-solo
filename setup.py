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
    python_requires='>=3.6',
    packages=find_packages(),
    url='https://github.com/lazybird/django-solo/',
    author='lazybird',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    include_package_data=True,
    zip_safe=False,
    license='Creative Commons Attribution 3.0 Unported',
    classifiers=[
        'Framework :: Django :: 2.2',
        'Framework :: Django :: 3.2',
        'Framework :: Django :: 4.0',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ]
)
