# Docker file for the Translator Knowledge Graph Beacon
FROM python:3.6

WORKDIR /home

COPY client client
COPY ontology ontology
COPY server server

RUN pip install client/ && pip install ontology/ && pip install --no-cache-dir -r server/requirements.txt

WORKDIR /home/server

EXPOSE 8080

ENTRYPOINT ["python3"]

CMD ["-m", "swagger_server"]
