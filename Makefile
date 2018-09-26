install:
	make configure
	pip install ontology/
	pip install client/
	pip install server/

# Creating the configuration file without installing
configure:
	cp -n client/beacon_controller/config/config.yaml-template client/beacon_controller/config/config.yaml
	cp -n docker-compose.yaml-template docker-compose.yaml

run:
	cd server && python -m swagger_server

docker-build-biolink:
	docker build -t ncats:biolink .

docker-build-rkb:
	docker build -t ncats:rkb .

docker-build-rtx:
	docker build -t ncats:rtx .

docker-run-biolink:
	docker run -d --rm --name biolink -p 8078:8080 ncats:biolink

docker-run-rkb:
	docker run -d --rm --name rkb -p 8075:8080 ncats:rkb

docker-run-rtx:
	docker run -d --rm --name rtx -p 8074:8080 ncats:rtx

docker-stop-biolink:
	docker stop biolink

docker-stop-rkb:
	docker stop rkb

docker-stop-rtx:
	docker stop rtx
