# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Invenio user management and authentication."""

import os

from setuptools import find_packages, setup

readme = open('README.rst').read()
history = open('CHANGES.rst').read()

tests_require = [
    'Flask-CeleryExt>=0.2.2',
    'Flask-Mail>=0.9.1',
    'check-manifest>=0.25',
    'coverage>=4.0',
    'isort>=4.2.2',
    'mock>=2.0.0',
    'pydocstyle>=1.0.0',
    'pytest-cov>=1.8.0',
    'pytest-flask>=0.10.0',
    'pytest-pep8>=1.0.6',
    'pytest>=2.8.0',
    'selenium>=3.0.1',
]

extras_require = {
    ':python_version=="2.7"': [
        'ipaddr>=2.1.11',
    ],
    'celery': [
        'celery>=3.1.0,<4.0',
    ],
    'docs': [
        'Sphinx>=1.4.2,<1.6',
    ],
    'mysql': [
        'invenio-db[versioning,mysql]>=1.0.0b8',
    ],
    'postgresql': [
        'invenio-db[versioning,postgresql]>=1.0.0b8',
    ],
    'sqlite': [
        'invenio-db[versioning]>=1.0.0b8',
    ],
    'admin': [
        'invenio-admin>=1.0.0b3',
    ],
    'tests': tests_require,
}

extras_require['all'] = []
for name, reqs in extras_require.items():
    if name[0] == ':':
        continue
    if name in ('mysql', 'postgresql', 'sqlite'):
        continue
    extras_require['all'].extend(reqs)

setup_requires = [
    'Babel>=1.3',
    'pytest-runner>=2.6.2',
]

install_requires = [
    'Flask-BabelEx>=0.9.3',
    'Flask-Breadcrumbs>=0.3.0',
    'Flask-KVSession>=0.6.1',
    'Flask-Login>=0.3.0',
    'Flask-Menu>=0.4.0',
    'Flask-Security>=3.0.0',
    'Flask-WTF>=0.13.1',
    'Flask>=0.11.1',
    'future>=0.16.0',
    # Not using 'ipaddress' extras for SQLALchemy-Utils in favor of
    # direct 'ipaddr' version marker (issues with Python3 builds on Travis).
    'SQLAlchemy-Utils>=0.31.0',
    'cryptography>=2.1.4',
    'invenio-i18n>=1.0.0b4',
    'maxminddb-geolite2>=2017.404',
    'passlib>=1.7.1',
    'pyjwt>=1.5.0',
    'redis>=2.10.5',
    'simplekv>=0.11.2',
    'ua-parser>=0.7.3',
]

packages = find_packages()

# Get the version string. Cannot be done with import!
g = {}
with open(os.path.join('invenio_accounts', 'version.py'), 'rt') as fp:
    exec(fp.read(), g)
    version = g['__version__']

setup(
    name='invenio-accounts',
    version=version,
    description=__doc__,
    long_description=readme + '\n\n' + history,
    keywords='invenio accounts user role login',
    license='MIT',
    author='CERN',
    author_email='info@inveniosoftware.org',
    url='https://github.com/inveniosoftware/invenio-accounts',
    packages=packages,
    zip_safe=False,
    include_package_data=True,
    platforms='any',
    entry_points={
        'flask.commands': [
            'roles = invenio_accounts.cli:roles',
            'users = invenio_accounts.cli:users',
        ],
        'invenio_admin.views': [
            'invenio_accounts_user = invenio_accounts.admin:user_adminview',
            'invenio_accounts_role = invenio_accounts.admin:role_adminview',
            'invenio_accounts_session = '
            'invenio_accounts.admin:session_adminview',
        ],
        'invenio_base.api_apps': [
            'invenio_accounts_rest = invenio_accounts:InvenioAccountsREST',
        ],
        'invenio_base.apps': [
            'invenio_accounts_ui = invenio_accounts:InvenioAccountsUI',
        ],
        'invenio_base.blueprints': [
            'invenio_accounts = invenio_accounts.views.settings:blueprint',
        ],
        'invenio_celery.tasks': [
            'invenio_accounts = invenio_accounts.tasks',
        ],
        'invenio_db.alembic': [
            'invenio_accounts = invenio_accounts:alembic',
        ],
        'invenio_db.models': [
            'invenio_accounts = invenio_accounts.models',
        ],
        'invenio_i18n.translations': [
            'messages = invenio_accounts',
        ],
    },
    extras_require=extras_require,
    install_requires=install_requires,
    setup_requires=setup_requires,
    tests_require=tests_require,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Development Status :: 4 - Beta',
    ],
)
