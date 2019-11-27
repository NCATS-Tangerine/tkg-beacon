from setuptools import setup

setup(
    name="translator-knowledge-beacon",
    url="https://github.com/NCATS-Tangerine/translator-knowledge-beacon",
    version = "1.3.0",
    packages = [
        'beacon_controller',
        'beacon_controller.controllers',
        'beacon_controller.database',
        'config',
        'data'
    ],
    include_package_data=True,
    install_requires=[
        'BiolinkMG',
        'neomodel',
        'pandas',
        'cachetools',
        'tornado',
        'requests',
        'flask',
        'pyyaml',
        'connexion == 1.1.15',
        'python_dateutil',
        'setuptools >= 21.0.0',
        'prefixcommons',
        'bmt',
    ]
)
