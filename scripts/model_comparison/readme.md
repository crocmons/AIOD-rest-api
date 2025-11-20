# Comparison to Conceptual Model

The REST API aims to implement the conceptual model definitions.
However, the implementation may drift apart from the conceptual model over time due to
practical reasons (e.g., no time to process updates).
The `compare.py` script can be used to compare the implementation in the REST API with the
definitions in the conceptual model.

## Requirements

Files:

 - The REST API code repository
 - The `model-export.json` file from the `metadata-schema` repository's `export` directory

Python environment:

 - The dependencies of the REST API need to be installed, as the code will import its modules.
 - The `pandas` package needs to be installed

To install the environment, from the root of the REST API repository execute:
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install uv
uv pip install -r pyproject.toml
uv pip install pandas
```

## Usage
Invoke the `compare.py` script, specifying the location of the REST API's `src` directory and the model export file:

```bash
python compare.py <source_path> <conceptual_model_path>
```

For example:
```bash
python compare.py /path/to/rest/api/src /path/to/model-export.json
```

To see all available options:
```bash
python compare.py --help
```

The `compare.py` script may need to be updated over time:

 - `class_maps`: mapping to clarify when the implemented name of a class differs from the name in the definition.
 - `property_renames_by_class`: mapping to clarify for each class when the implemented name of a property differs from the name in the definition.
 - `class_ignores`: classes which are implemented but should not be reported, useful to hide implementation details.
 - `property_suffix_ignores`: suffixes of properties which should not be reported, useful to hide implementation details.

Note that to compare implemented and defined names (for both classes and properties) they are typically _normalized_ by converting them to lowercases and removing spaces and underscores.
Some of the mappings above use normalized names for some of the keys, this is documented in the `compare.py` file.

## Limitations
This tool does not identify properties which are implemented at the wrong level of the hierarchy.
For example, given the situation:

 - `B` is defined as a subclass of `A`
 - `B` is implemented as a subclass of `A`
 - property `c` is defined on `A`
 - property `c` is implemented in `B`

then the tool will report that `A` is missing `c` and `B` has an extra `c` property.
