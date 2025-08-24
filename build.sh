#!/bin/bash

docker image rm bh1750-mqtt
docker build -t bh1750-mqtt .
