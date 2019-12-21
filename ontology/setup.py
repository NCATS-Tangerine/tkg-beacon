from setuptools import setup

setup(
    name="beacon_ontology",
    version="1.1",
    author="lance@starinformatics.com",
    description="A python implementation of the biolink model",
    packages=['beacon_ontology'],
    install_requires=[
        'pyyaml',
        'requests'
    ]
)
