## TKG Beacon

For wrapping Translator Knowledge Graph compliant Neo4j databases.

Two options: 

1. Run the wrapper directly
2. Run the wrapper within Docker

## 1. Directly (code snippets are for Linux)

### Getting started

Create a fresh virtual environment
```
virtualenv -p python3.5 venv
source venv/bin/activate
```

Install the project requirements:
```
pip install -r requirements.txt
```

Setup the config file by copying the template file:
```
cp config.yaml-template config.yaml
``` 
Change the database settings in `config.yaml` to match the address and credentials of the wanted neo4j database.

Navigate into the `/server` directory and run:
```
python setup.py install
```

Then navigate into the `/ontology` and `/client` directories and do the same.

Then navigate into the `/server` directory and run the program with:
```
python -m swagger_server
```

The Swagger UI can be found at `{basepath}/ui/`, e.g. `localhost:8080/ui/`

### Configuring the beacon
Settings should be in `config.yaml`.
Change the database address (bolt protocol), username, and password to the Neo4j database you would like to wrap.

Setting `filter_biolink` to `True` will ignore all categories that are non-Biolink compliant if a concept has more than one category. If only one category exists for a particular concept, the concept will be reported by the beacon as `"named thing"`.

## 2. Running under Docker

## Installation of Docker

If you choose to run the dockerized versions of the applications, you'll obviously need to [install Docker first](https://docs.docker.com/engine/installation/) in your target Linux operating environment (bare metal server or virtual machine running Linux).

For our installations, we typically use Ubuntu Linux, for which there is an [Ubuntu-specific docker installation using the repository](https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/#install-using-the-repository).
Note that you should have 'curl' installed first before installing Docker:

```
$ sudo apt-get install curl
```

For other installations, please find instructions specific to your choice of Linux variant, on the Docker site.

## Testing Docker

In order to ensure that docker is working correctly, run the following command:

```
$ sudo docker run hello-world
```

This should result in the following output:
```
Unable to find image 'hello-world:latest' locally
latest: Pulling from library/hello-world
ca4f61b1923c: Pull complete
Digest: sha256:be0cd392e45be79ffeffa6b05338b98ebb16c87b255f48e297ec7f98e123905c
Status: Downloaded newer image for hello-world:latest

Hello from Docker!
This message shows that your installation appears to be working correctly.

To generate this message, Docker took the following steps:
 1. The Docker client contacted the Docker daemon.
 2. The Docker daemon pulled the "hello-world" image from the Docker Hub.
    (amd64)
 3. The Docker daemon created a new container from that image which runs the
    executable that produces the output you are currently reading.
 4. The Docker daemon streamed that output to the Docker client, which sent it
    to your terminal.

To try something more ambitious, you can run an Ubuntu container with:
 $ docker run -it ubuntu bash

Share images, automate workflows, and more with a free Docker ID:
 https://cloud.docker.com/

For more examples and ideas, visit:
 https://docs.docker.com/engine/userguide/
```

## Installing Docker Compose

You will then also need to [install Docker Compose](https://docs.docker.com/compose/install/) alongside Docker on your target Linux operating environment.

Note that under Ubuntu, you need to run docker (and docker-compose) as 'sudo'. 

## Testing Docker Compose

In order to ensure Docker Compose is working correctly, issue the following command:
```
$ docker-compose --version
docker-compose version 1.18.0, build 8dd22a9
```
Note that your particular version and build number may be different than what is shown here. We don't currently expect that docker-compose version differences should have a significant impact on the build, but if in doubt, refer to the release notes of the docker-compose site for advice.

## Configuring the Application

Copy the config.yaml-template into config.yaml and customize it to the credentials of your TKG database. 

Also make a copy of the docker-compose.yaml-template into docker-compose.yaml and customize the Neo4j credentials to those of your TKG database. Alternately, set the NEO4J_AUTH environment variable to these credentials.

To build the Docker containers, run the following command

```
 $ cd ..  # make sure you are back in the root project directory
 $ sudo docker-compose -f docker-compose.yaml build
```

This command make take some time to execute, as it is downloading and building your docker containers.

To run the system, run the following command:

```
$ sudo docker-compose up
```

To shut down the system, run the following:

```
$ sudo docker-compose down
```

You can also selectively shut down (and start up) the web api and database Docker containers, as follows:

```
$ sudo docker-compose down tkg-api
$ sudo docker-compose down tkg-db
```
and

```
$ sudo docker-compose up tkg-db
$ sudo docker-compose up tkg-api

```
