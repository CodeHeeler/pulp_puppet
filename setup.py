#!/usr/bin/env python3

from setuptools import setup

requirements = [
    'pulpcore-plugin',
]

setup(
    name='pulp-puppet',
    version='3.0.0a1.dev1',
    description='Puppet plugin for the Pulp Project',
    license='GPLv2+',
    python_requires='>=3.5',
    author='Pulp Project Developers',
    author_email='pulp-dev@redhat.com',
    url='https://github.com/pulp/pulp_puppet',
    install_requires=requirements,
    include_package_data=True,
    packages=['pulp_puppet', 'pulp_puppet.app'],
    classifiers=(
        'License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)',
        'Operating System :: POSIX :: Linux',
        'Framework :: Django',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ),
    entry_points={
        'pulpcore.plugin': [
            'pulp_puppet = pulp_puppet:default_app_config',
        ]
    }
)
