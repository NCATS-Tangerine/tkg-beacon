from setuptools import setup

setup(
    name = "beacon_controller",
    version = "1.0",
    author = "lance@starinformatics.com",
    description = "Implementation of the controller classes of the biolink beacon",
    packages = [
        'beacon_controller',
        'beacon_controller.controllers',
        'beacon_controller.database'
    ],
    include_package_data=True
)
