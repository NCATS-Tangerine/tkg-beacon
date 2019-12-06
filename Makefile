configure:
	cp config/config.yaml-template config/config.yaml

install:
	python -m pip install .
	python -m pip install beacon/
	python -m pip install ontology/

dev-install:
	python -m pip install -e .
	python -m pip install beacon/
	python -m pip install ontology/

run:
	cd beacon && python -m swagger_server

docker-build-biolink:
	docker build -t ncats:biolink .

docker-build-semmeddb:
	docker build -t ncats:semmeddb .

docker-build-rtx:
	docker build -t ncats:rtx .

docker-run-biolink:
	docker run -d --rm --name biolink -p 8078:8080 ncats:biolink

docker-run-semmeddb:
	docker run -d --rm --name semmeddb -p 8075:8080 ncats:semmeddb

docker-run-rtx:
	docker run -d --rm --name rtx -p 8074:8080 ncats:rtx

docker-stop-biolink:
	docker stop biolink

docker-stop-semmeddb:
	docker stop semmeddb

docker-stop-rtx:
	docker stop rtx

docker-logs-biolink:
	docker logs biolink

docker-logs-semmeddb:
	docker logs semmeddb

docker-logs-rtx:
	docker logs rtx
