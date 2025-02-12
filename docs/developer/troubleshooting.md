## Logging
The REST API uses the built-in [`logging`](https://docs.python.org/3/library/logging.html) module for its logging.
The [log level](https://docs.python.org/3/library/logging.html#logging-levels) for the configuration can be configured
in the `src/config.override.toml` file, as `dev.log_level`.

## Navigating the logs
The REST API will provide an error reference with each exception it raises.
For example, trying to access a dataset that does not exist may result in:

```json
{
  'detail': "Dataset '42' not found in the database.",
  'reference': 'd47cb85f6cf64c158dbb65e1a891903f'
}
```

To figure out what lead to this error, you can reference the logs.
Unexpected errors, i.e., uncaught ones, are logged at `logging.ERROR` level.
Other errors, such as the one above, are logged at `logging.DEBUG` level.
By default, logging output is at `logging.INFO` level, so if you want to capture all warnings you
must first set it to `logging.DEBUG`.

You can find the error in the docker logs as `docker logs CONTAINER_NAME 2>&1 | grep -e "REFERENCE"`,
e.g.,`docker logs apiserver 2>&1 | grep -e "d47cb85f6cf64c158dbb65e1a891903f"`. The log message will 
contain information about the type of request (`GET`) the path and query (`/datasets/v1/42`), and 
the body content (in the case of requests that have one).