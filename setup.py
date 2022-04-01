from __future__ import annotations

import os
from pathlib import Path

from setuptools import find_packages, setup

README = (Path(__file__).parent / 'README.md').read_text()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))
version = __import__('stepik_plugins_client').get_version()

setup(
    name='stepik-plugins-client',
    version=version,
    packages=find_packages(include=['stepik_plugins_client*']),
    include_package_data=True,
    author='Hyperskill Team',
    description='A client for Stepik plugins',
    long_description=README,
    url='https://stepik.org',
    install_requires=[
        'oslo.messaging==4.4.0',
        'pytz==2022.1',
        'structlog==21.5.0',
        'voluptuous==0.12.2',
    ],
)
