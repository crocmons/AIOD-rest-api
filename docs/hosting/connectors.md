# Connectors for AI-on-Demand
[//]: # (The section below is referenced in "index.md", if you change lines 3-22, update the reference accordingly.)

To start connector services that automatically index data from external platforms into the metadata catalogue,
you must specify their docker-compose profiles (as defined in the `docker-compose.yaml` file).
For example, you can use the following commands when starting the connectors for OpenML and Zenodo.

=== "Shorthand"
```commandline
./scripts/up.sh openml zenodo-datasets
```
=== "Docker Compose"
```commandline
docker compose --profile openml --profile zenodo-datasets --env-file=.env --env-file=override.env up -d
```

The full list of connector profiles are:

- openml: indexes datasets and models from OpenML.
- zenodo-datasets: indexes datasets from Zenodo.
- huggingface-datasets: indexes datasets from Hugging Face.
- aibuilder: indexes models on AI Builder
- examples: fills the database with some example data. Do not use in production.

[//]: # (The section above is referenced in "index.md", if you change lines 3-22, update the reference accordingly.)

## Configuring AIBuilder connector
To access the AIBuilder API you need to provide a valid API token through the `AIBUILDER_API_TOKEN` variable. \
Use the `override.env` file for that as explained above. \
Please note that for using the url of the `same_as` field of the AIBuilder models, you will need to substitute `AIBUILDER_API_TOKEN` on the url for your actual API token value.
