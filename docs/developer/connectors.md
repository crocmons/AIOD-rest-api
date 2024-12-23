
#### Using connectors
You can specify different connectors using

```bash
docker compose --profile aibuilder --profile examples --profile huggingface-datasets --profile openml --profile zenodo-datasets up -d
docker compose --profile aibuilder --profile examples --profile huggingface-datasets --profile openml --profile zenodo-datasets down
```

Make sure you use the same profile for `up` and `down`, or use `./scripts/down.sh` (see below),
otherwise some containers might keep running.

##### Configuring AIBuilder connector
To access the AIBuilder API you need to provide a valid API token through the `AIBUILDER_API_TOKEN` variable. \
Use the `override.env` file for that as explained above. \
Please note that for using the url of the `same_as` field of the AIBuilder models, you will need to substitute `AIBUILDER_API_TOKEN` on the url for your actual API token value.
