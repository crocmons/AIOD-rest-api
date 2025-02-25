#!/bin/bash

echo "Error: this in only an example. Should be run on a dedicated server (such as test.openml.org)"
exit 1

docker run \
	-p 8989:8989 \
	--name keycloak \
	-d \
	--restart unless-stopped \
	--network sql-network \
	-e KEYCLOAK_ADMIN=administrator \
	-e KEYCLOAK_ADMIN_PASSWORD=the_password_that_you_created \
	aiod_keycloak:latest \
		start-dev \
		--db-username root \
		--db-password ok \
		--db-url-host sqlserver \
		--db-url-port 3306 \
		--db-url-database keycloak \
		--http-port 8989 \
		--hostname-url https://test.openml.org/aiod-auth \
		--hostname-admin-url https://test.openml.org/aiod-auth \
		--hostname-strict-backchannel=true \
		--db mysql
