from setuptools import setup
description = "Burp interface with typing hints"
readme = open("README.rst").read()

setup(
    name='burp',
    version='1.27',
    packages=['burp'],
    url='https://github.com/elnerd/burp-interfaces',
    license='MIT',
    author='Erlend Leiknes',
    author_email='dev@leikn.es',
    description='Annotated burp interfaces for python/jython',
    install_requires=[],
    long_description=readme,
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: Jython',
        'Intended Audience :: Developers',
    ]
)
