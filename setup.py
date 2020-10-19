#!/usr/bin/env python3

import os
from setuptools import find_packages, setup
from setuptools.command.install import install
from setuptools.command.develop import develop


class ShivInstallCommand(install):
    def run(self):
        os.system("shiv \
            --compressed \
            -o OpenDashboardGateway-AssettoCorsa.pyz \
            -e assetto_corsa_gateway.main:main \
            -r requirements.txt \
            ."
        )


class ProtocBuildCommand(develop):
    def run(self):
        os.system("protoc --python_out=./assetto_corsa_gateway/ ./open_dashboard_idl/open_dashboard.proto")

setup(
    name="assetto_corsa_gateway",
    version="0.0.1",
    packages=find_packages(),
    include_package_data=True,

    cmdclass={
        'shiv': ShivInstallCommand,
        'protoc': ProtocBuildCommand,
    },
)