install:
	cp -n config.yaml-template config.yaml
	pip install -r requirements.txt
	cd server/ && python setup.py install
	cd client/ && python setup.py install
	cd ontology/ && python setup.py install

# Creating the configuration file without installing
configure:
	cp -n config.yaml-template config.yml
	cp -n docker-compose.yaml-template docker-compose.yaml

run:
	cd server && python -m swagger_server
