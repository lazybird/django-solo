from setuptools import setup, find_packages
import solo


setup(
    name='django-solo',
    version=solo.__version__,
    description=solo.__doc__,
    packages=find_packages(),
    url='http://github.com/lazybird/django-solo/',
    author='lazybird',
    include_package_data=True,
    zip_safe=False,
    license='Creative Commons Attribution 3.0 Unported',
)
