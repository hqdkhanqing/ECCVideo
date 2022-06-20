version ?= 1.0.0


.PHONY: build
build: 
	cd ../ && docker build -f docker/orchestrator/Dockerfile -t edgeai/orchestrator:${version} .
	cd ../ && docker build -f docker/controller/Dockerfile -t edgeai/controller:${version} .
