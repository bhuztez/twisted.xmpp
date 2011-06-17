#!/usr/bin/env python2

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='twisted.xmpp',
    version='0.0',

    url='',
    description='Twisted XMPP Library',

    classifiers = [
        "Development Status :: 1 - Planning",
        "Framework :: Twisted",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 2.7",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],

    author='bhuztez',
    author_email='bhuztez@gmail.com',

    requires=['Twisted (>= 11.0)'],

    namespace_packages=['twisted'],
    packages = ['twisted', 'twisted.xmpp'],
    package_data={
        'twisted': ['plugins/twisted_xmppd.py'],
    },

    zip_safe = False,
)


