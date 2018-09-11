install:
	cp -n config.yaml-template config.yaml
	pip install -r requirements.txt
	cd server/ && python setup.py install
	cd client/ && python setup.py install
	cd ontology/ && python setup.py install

# Creating the configuration file without installing
configure:
	cp -n client/beacon_controller/config/config.yaml-template client/beacon_controller/config/config.yaml
	cp -n docker-compose.yaml-template docker-compose.yaml

run:
	cd server && python -m swagger_server

docker-build:
	docker build -t ncats:${tag} .

docker-run-biolink:
	docker run -d --rm -p 8078:8080 ncats:biolink

docker-run-rkb:
	docker run -d --rm -p 8075:8080 ncats:rkb

docker-run-rtx:
	docker run -d --rm -p 8074:8080 ncats:rtx
