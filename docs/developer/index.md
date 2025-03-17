# Metadata Catalogue API

The metadata catalogue is a collection of AI-related metadata from a wide range of sources.
This page contains design documentation, if you are interested in how to set up your
development environment, please see
["setting up your development environment"](../contributing.md#setting-up-a-development-environment).

Its REST API service is, in effect, not much more than a way to create, read, update, and delete (CRUD) metadata.
For this, the project uses as core building blocks
[FastAPI](https://fastapi.tiangolo.com/) for the web server and routing,
[SQLModel](https://sqlmodel.tiangolo.com/) for model validation and persistence to a
[MySQL](https://hub.docker.com/_/mysql) database.
In turn, [SQLModel](https://sqlmodel.tiangolo.com/) is a package that brings together
[Pydantic](https://docs.pydantic.dev/latest/) for model validation and
[SQLAlchemy](https://www.sqlalchemy.org/) for persistence to the database.
If you are not familiar with these technologies, we strongly encourage you to read their
"getting started" pages (or similar).
We will generally not repeat their documentation here, we do provide slightly more context
of their usage in this project in the admonitions below.

??? info "FastAPI"

    FastAPI allows us to easily construct REST API paths on our web server. For example:
    ```python
    @app.get("/datasets/{identifier})
    def get_dataset(identifier: int, user=Depends(user_or_raise)) -> Dataset:
        ... # fetch a dataset
        return dataset
    ```
    Creates an endpoint for `GET` requests, automatically parses the identifier from the
    path information as an integer (providing an error if it is absent or not an integer),
    and decodes the authentication information in the HTTP header to user information for
    use in the server back-end. It can then return an object which is serialized to JSON
    in the body of the response. For this parsing, FastAPI relies on Pydantic (see below).

    Usage of FastAPI is mostly limited to `src/main.py` and routers in `src/routers`:
    the modules that define our web endpoints. You will often see calls to decorating
    methods directly, e.g., `app.get("/datasets/{identifier})(get_dataset)` insteaf of the
    `@app.get` decorator syntax.

??? info "Pydantic"

    Pydantic is a library for runtime data validation. Normally, Python does not care about
    type hints at runtime, e.g., the code below is fine and runs without errors:

    ```python
    from dataclasses import dataclass

    @dataclass
    class Foo:
        x: int

    bar = Foo(x="This is a string, not an integer.")
    ```

    Using Pydantic's `BaseModel`, typehints are used to validate data at runtime, raising
    an error if the data value does not adhere to the constraints of the type. For example,
    the code below raises a `ValidationError`:

    ```python
    from pydantic import BaseModel

    class Foo(BaseModel):
        x: int

    bar = Foo(x="This is a string, not an integer.")
    ```

    Using Pydantic, we can annotate our classes, such that FastAPI knows how to validate
    the input data on requests. For example, to ensure a metadata asset uploaded by a user
    adheres to our schema definition.

    Pydantic is used throughout the project, especially for model definitions in
    `src/database/` and is frequently indirectly through SQLModel (below).

    Pydantic and FastAPI also work together to automatically create an
    [OpenAPI](https://www.openapis.org/) schema definition, which is used to provide
    auto-generated docs.

??? info "SQLAlchemy"

    SQLAlchemy allows us to define tables in our database through Python code, query it, and
    load it into Python objects with it's object-relational mapping (ORM) layer.
    This allows us to write something like:

    ```python
    # DbSession is a function defined by the metadata catalogue to ensure only one 'engine'
    # gets created, but simply returns an SQLAlchemy session object.
    with DbSession() as session:
        dataset = session.get(Dataset, identifier)
    print(f"We loaded dataset {dataset.name} from the database!")
    ```


??? info "SQLModel"

    SQLModel brings together SQLAlchemy and Pydantic.
    Where Pydantic can help us define type constraints for our Python objects,
    SQLAlchemy helps us define type constraints for the database.
    With SQLModel, we can define these two together on one model instead.
    This is useful, since they are often updated in sync (e.g.,
    an attribute gets added to a model, we also need to add a column to the respective table).
    For example:

    ```python
    class Foo(SQLModel, table=True):  # Note the inheritance from SQLModle
        __tablename__ = "foo"  # Give a custom name to the database table for this type
        name: str | None = Field(
            max_length=128,
            default=None,
            description="The name of this foo.",
            schema_extra={"example": "Alecia Bobbus"},
        )
    ```

    The `Foo` object can now be used directly with `SQLAlchemy` as it is mapped to the "foo" table.
    The attribute specification ensures there is a column for strings (varchar in MySQL), which is
    nullable (note that `string | None` typehint). The character limit of 128 is defined on the
    database level, but it is also used for runtime validation by Pydantic. The description and
    `schema_extra` are used from `Foo`'s schema description in the REST API.

    The conceptual model is implemented as a large inheritance hierarchy, and at the top we have a
    SQLModel class, ensuring that we can do both persistence to the database and model validation.
    More on this inheritance structure below.

## Request Flow

The data in our database is stored in the format defined by (the implementation of) our
[conceptual model](schema/index.md).
When the user requests an item, such as a dataset, it can be returned in AIoD format,
or converted to any supported format, as requested by the user. For datasets,
we will for instance support [schema.org](https://schema.org/Dataset) and
[DCAT-AP](https://op.europa.eu/en/web/eu-vocabularies/dcat-ap).

Requesting a dataset will therefore be simply:

![Get dataset UML](../media/GetDatasetUML.png)

## Other Services

In this project, you will find a few configurations and services which are strongly related to
the REST API, and are often deployed together. These are:

  * An [authentication](authentication.md) service based on keycloak.
  * A [search index](elastic_search.md) based on elastic search and log stash.
  * A number of [connectors](../hosting/connectors.md): code which periodically indexes data on
    other platforms, such as [Zenodo](https://zenodo.org), and stores it in the metadata catalogue.

