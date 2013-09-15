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
    classifiers=[
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: Creative Commons Attribution 3.0 Unported',
        'Operating System :: OS Independent',
        'Topic :: Software Development'
    ],
)
