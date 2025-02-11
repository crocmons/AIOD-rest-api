#!/bin/bash
# convenience script to revert back to a clean state.

DIR_SCRIPT=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
DIR_ROOT=$( dirname $DIR_SCRIPT )
DIR_DATA=$DIR_ROOT/data

DIR_MYSQL=$DIR_DATA/mysql
DIR_CONNECTORS=$DIR_DATA/connectors
DIR_DELETION=$DIR_DATA/deletion
DIR_ELASTIC=$DIR_DATA/elasticsearch
DIR_KEYCLOAK=$DIR_DATA/keycloak/data

sudo find $DIR_CONNECTORS -type f ! -name .gitkeep -delete
sudo find $DIR_DELETION -type f ! -name .gitkeep -delete
sudo rm -rf $DIR_MYSQL/*
touch $DIR_MYSQL/.gitkeep
sudo rm -rf $DIR_ELASTIC/*
sudo rm -rf $DIR_KEYCLOAK/tmp
sudo rm -rf $DIR_KEYCLOAK/h2
touch $DIR_ELASTIC/.gitkeep
