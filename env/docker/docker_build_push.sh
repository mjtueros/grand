#! /bin/bash

tag="0.2"

docker build -f Dockerfile_grand_env_dev . --tag=grand_env:$tag

docker tag grand_env:$tag jcolley/grand:$tag
docker push jcolley/grand:$tag