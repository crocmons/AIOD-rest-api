# Elastic Search

Elastic Search indexes the information in the database for quick retrieval, facilitating endpoints 
that can search through assets with loosely matching queries and give relevancy-ranked suggestions.

## Indexing the Database using Logstash
Elastic Search keeps independent indices for various assets in the database, and achieves this by:

 * Creating an initial index
 * Populating it based on the information already in the database
 * Updating the index with new information periodically, removing old entries if necessary

Because the logic for these steps is very similar for the different assets, we generate various
scripts to create and maintain the elastic search indices. We use [Logstash](https://www.elastic.co/logstash)
to process the data from our database and export it to Elastic Search.

This happens through two container services: 

 * `es_logstash_setup`: Generates the common scripts for use by logstash, and creates the Elastic Search indices if necessary.
    This is a short-running service that only runs on startup, exiting when its done.
 * `logstash`: Continually monitors the database and updates the Elastic Search indices.

### Logstash Setup

The `es_logstash_setup` service executes two important roles: generating logstash files and creating Elastic Search indices.

The `src/logstash_setup/generate_logstash_config_files.py` file generates logstash files based on the
templates provided in the `src/logstash_setup/templates` directory. The generated files are placed
into subdirectories of the `logstash/config` directory, along with predefined files.

For syncing the Elastic Search index, logstash requires SQL files that extract the necessary data from the database.
These are generated based on the `src/logstash_setup/templates/sql_{init|sync|rm}.py` files:

 * The `sql_init.py` file defines the query template that finds the data that should be included in the index if it is populated from scratch.
 * The `sql_sync.py` file defines the query template that finds the data that has been updated since the last creation or synchronization, so that the ES index can be updated efficiently.
 * The `sql_rm.py` file defines the query template that finds the data that should be removed from the index.

It also generates the configuration files needed for Logstash to run the sync scripts:

 * `config.py`: used to generate `logstash.yml`, the general configuration.
 * `init_table.py`: contains the configuration that is needed to run the queries from `sql_init.py`, and defines them for each asset that needs to be indexed.
 * `sync_table.py`: contains the configuration that is needed to run the queries from `sql_sync.py` and `sql_rm.py` scripts, and defines them for each asset that needs to be synced.

All generated files contain the preamble defined in `file_header.py`.
Additionally, the `logstash/config/config` directory contains additional files used for the configuration of logstash, such as the JVM options.

### Creating a New Index
To create a new index for an asset supported in the metadata catalogue REST API, you simply need to create the respective "search router", more on that below.

## Elastic Search in the Metadata Catalogue
The metadata catalogue provides REST API endpoints to allow querying elastic search in a uniform manner.
While the Elastic Search can be exposed directly in production, this unified endpoint allows us to provide more structure and better automated documentation.
It also avoids requiring the user to learn the Elastic Search query format.

### Creating a New Search
To extend  Elastic Search to a new asset type, create a search router, similar to those in `src/routers/search_routers/`.
Simply inherit from the base `SearchRouter` class defined in `src/routers/search_router.py` and define a few properties:

```python 
    @property
    def es_index(self) -> str:
        return "case_study"
```
The `es_index` property defines the name of the index. It is how it is known by Elasic Search, and should match the name of the table in the database.

```python
    @property
    def resource_name_plural(self) -> str:
        return "case_studies"
```

The `resource_name_plural` is used to define the path of the REST API endpoint, e.g.: `api.aiod.eu/search/case_studies`.

```python
@property
def resource_class(self):
    return CaseStudy
```

The `resource_class` property contains a direct reference to the object it indexes, which is used when returning expanded responses from the ES query ("get all").

```python
    @property
    def extra_indexed_fields(self) -> set[str]:
        return {"headline", "alternative_headline"}
```

The `extra_indexed_fields` property contains the fields of the entity that should be included in the index other than the `global_indexed_fields` found in the `SearchRouter` class.

```python
    @property
    def linked_fields(self) -> set[str]:
        return {
            "alternate_name",
            "application_area",
            "industrial_sector",
            "research_area",
            "scientific_domain",
        }
```
The `linked_fields` property contains the fields of the entity which refer to external tables and should be included in the index.

By creating a new `SearchRouter` (and adding it to the router list), the script which generates the logstash files will automatically include it.

## Configuration
Besides the aforementioned configuration files, the elastic search configuration is located at `es/elasticsearch.yml`, but shouldn't need much configuration.
Some aspects of both Logstash and Elastic Search are to be configured through environment variables through the `override.env` file (defaults in `.env`).
Most notable one of these are the password for Elastic Search and the JVM resource options.