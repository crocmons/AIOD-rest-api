#!/usr/bin/env bash
docker exec -it sqlserver mysql -uroot -pok --database=aiod -e "UPDATE alembic_version SET version_num = '$1'"
