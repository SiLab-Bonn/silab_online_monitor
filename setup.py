#!/usr/bin/env python
import os
from setuptools import setup, find_packages  # This setup relies on setuptools since distutils is insufficient and badly hacked code

version = '0.2.3'
author = 'David-Leon Pohl'
author_email = 'pohl@physik.uni-bonn.de'

# requirements for core functionality from requirements.txt
with open('requirements.txt') as f:
    install_requires = f.read().splitlines()

setup(
    name='silab_online_monitor',
    version=version,
    description='Specific converters and receivers for SiLab data acquisition systems to be used with the generic online_monitor python package.',
    url='https://github.com/SiLab-Bonn/silab_online_monitor',
    license='MIT License',
    long_description='',
    author=author,
    maintainer=author,
    author_email=author_email,
    maintainer_email=author_email,
    install_requires=install_requires,
    packages=find_packages(),
    include_package_data=True,  # accept all data files and directories matched by MANIFEST.in or found in source control
    package_data={'': ['README.*', 'VERSION'], 'docs': ['*'], 'examples': ['*']},
    keywords=['silab', 'online monitor', 'real time plots'],
    platforms='any'
)

# print os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)) + r'/silab_online_monitor/producer_sim/'))
from online_monitor.utils import settings
settings.add_producer_sim_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)) + r'/silab_online_monitor/producer_sim')))
settings.add_converter_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)) + r'/silab_online_monitor/converter')))
settings.add_receiver_path(os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)) + r'/silab_online_monitor/receiver')))