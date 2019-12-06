## TKG Beacon

For wrapping Translator Knowledge Graph compliant Neo4j databases.

Python Beacon client https://github.com/NCATS-Tangerine/tkbeacon-python-client

## Getting Started

This project currently uses Python 3.7, and it is advised that you use this version.

### Configuring

You may create the configuration file `config/config.yaml` with the following command:
```
make configure
```
Change the database settings in `config/config.yaml` to match the address and credentials of the wanted neo4j database. Also set the beacon name appropriately. The name serves two functions: it shows up in the basepath, and it also determines the location of the metadata files. Setting `filter_biolink` to `True` will ignore all categories that are non-Biolink compliant if a concept has more than one category. If only one category exists for a particular concept, the concept will be reported by the beacon as `"named thing"`.

### Getting the data

The Cypher queries for the metadata endpoints are incredibly slow, and so we have opted to run them offline. The metadata should be contained in `data/{beacon name}/edge_summary.txt` and `data/{beacon name}/edge_summary.txt`. These files can be generated using the [KGX](https://kgx.readthedocs.io/en/latest/index.html) command line interface `neo4j-node-summary` and `neo4j-edge-summary` commands. The resulting files will need to be placed in `data/{beacon name}/`. Of course if you're giving your beaon a new name (not one of the defaults: "biolink", "semmeddb", "rtx") then you will have to create a new directory to hold its metadata.

### Running the application

There are two options for running this application:

1. Run the wrapper directly
2. Run the wrapper within Docker

#### 1. Directly (code snippets are for Linux)

Create a fresh virtual environment
```
virtualenv -p python3.7 venv
source venv/bin/activate
```
Once configuration is finished, you may install the application with:
```
make install
```
If you are developing the application and may be playing around with configurations, you can install it in developer mode instead (so that you will not need to re-install every time you make a change):
```
make dev-install
```
Finally, you can run the application with:
```
make run
```
Visit it at http://localhost:8080. The basepath will automatically contain `/beacon/{beacon name}/`, and you will be redirected appropriately.

### 2. Running under Docker

#### Installation of Docker

If you choose to run the dockerized versions of the applications, you'll obviously need to [install Docker first](https://docs.docker.com/engine/installation/) in your target Linux operating environment (bare metal server or virtual machine running Linux).

For our installations, we typically use Ubuntu Linux, for which there is an [Ubuntu-specific docker installation using the repository](https://docs.docker.com/engine/installation/linux/docker-ce/ubuntu/#install-using-the-repository).
Note that you should have 'curl' installed first before installing Docker:

```
$ sudo apt-get install curl
```

For other installations, please find instructions specific to your choice of Linux variant, on the Docker site.

#### Testing Docker

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

#### Installing Docker Compose

You will then also need to [install Docker Compose](https://docs.docker.com/compose/install/) alongside Docker on your target Linux operating environment.

Note that under Ubuntu, you may need to run docker (and docker-compose) as 'sudo'.

#### Testing Docker Compose

In order to ensure Docker Compose is working correctly, issue the following command:
```
$ docker-compose --version
docker-compose version 1.18.0, build 8dd22a9
```
Note that your particular version and build number may be different than what is shown here. We don't currently expect that docker-compose version differences should have a significant impact on the build, but if in doubt, refer to the release notes of the docker-compose site for advice.

#### Configuring the Application

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
