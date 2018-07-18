# Docker file for the Translator Knowledge Graph Beacon
FROM python:3

WORKDIR /home

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY client client
COPY ontology ontology
COPY server server

WORKDIR client

# The config,yaml file needs to be copied from the config.yaml-template 
# and customized to point to the Neo4j TKG database that you are wrapping
COPY config.yaml beacon_controller/config.yaml
RUN python setup.py install

WORKDIR ../ontology
RUN python setup.py install

WORKDIR ../server
RUN python setup.py install

ENTRYPOINT ["python", "-m", "swagger_server"]
