import dataclasses
import json
import sys
from pathlib import Path

import pandas as pd

from schema_inspector import get_initial_schema

IGNORES = []

# Some classes are implemented under a different name
# Implementation: Conceptual Model
class_maps = {
    "News": "News Item",
    "IndustrialSector": "Business Sector",
    "Turnover": "Company Revenue",
    "NumberOfEmployees": "Company Size",
    "AIoDEntryRead": "AIoD Entry",
}

# All names in this maps should be normalized
# Class: {Implementation: Conceptual Model}
property_renames_by_class = {
    "aiodentry": {"datecreated": "entrycreated", "datemodified": "modified"},
    "airesource": {
        "alternatename": "alternativename",
        "industrialsector": "businesssector",
        "ispartof": "partof",
    },
    "computationalasset": {"type": "computationalassettype"},
    "educationalresource": {
        "prerequisite": "prerequisiteknowledge",
        "targetaudience": "targetseducationallevel",
    },
    "event": {
        "status": "currenteventstatus",
        "mode": "usesmode",
    },
    "experiment": {"executionsettings": "exemplaryexecutionsettings"},
    "publication": {
        "isbn": "hasisbn",
        "issn": "hasissn",
    },
    "person": {"languages": "language"},
    "aiasset": {"license": "licence"},
    "runnabledistribution": {"deploymenttimemilliseconds": "deploymenttimemsec"},
}
# Some classes are artefacts of the implementation or are required for
# other parts of the system. We can ignore them in this comparison.
class_ignores = {
    # Classes defined for convenience to help with the conceptual model implementation
    "Taxonomy",
    "NamedRelation",
    "Text",
    "Body",
    # Classes defined for the REST API unrelated to the conceptual model
    "Bookmark",
    "AIoDEntryCreate",
}

property_suffix_ignores = {"_id", "_identifier", "__"}


def normalize(string: str) -> str:
    return string.casefold().replace(" ", "").replace("_", "")


def main():
    _, source_path, conceptual_model_path = sys.argv
    source_path = Path(source_path)
    assert source_path.exists() and source_path.is_dir(), (  # noqa: S101
        f"No source directory {source_path.absolute()} found."
    )
    conceptual_model_path = Path(conceptual_model_path)
    assert conceptual_model_path.exists() and conceptual_model_path.is_file(), (  # noqa: S101
        f"No conceptual model file {conceptual_model_path.absolute()} found."
    )

    implementation = load_implemented_schema(source_path)
    definition = json.loads(conceptual_model_path.read_text())
    conceptual_model = {clazz["name"]: clazz for clazz in definition["classes"]}

    report_differences(implementation, conceptual_model)


def load_implemented_schema(source_path) -> dict:
    implemented_classes, errors, class_hierarchy = get_initial_schema(source_path)
    for clazz, metadata in implemented_classes.items():
        metadata["parents"] = {}
        parents = class_hierarchy.get(clazz, [])[:]
        while parents:
            parent = parents.pop()
            if parent in ["SQLModel", "BaseModel"]:
                continue
            metadata["parents"][parent] = implemented_classes[parent]
            parents.extend(class_hierarchy.get(parent, []))

        all_properties = {name: property for name, property in metadata["properties"].items()}
        inherited_properties = {
            name: property
            for parent_name, parent in metadata["parents"].items()
            for name, property in parent["properties"].items()
            # If the name matches with a Base suffix, it should be considered as a direct definition
            # The structure of the code base has ItemBase defining properties which will be properties
            # of the table in the database, and Item defines the relationships to other tables.
            if parent_name != f"{clazz}Base"
        }
        metadata["inherited_properties"] = inherited_properties
        metadata["direct_properties"] = {
            k: v for k, v in all_properties.items() if k not in inherited_properties
        }

    implemented_classes = {
        class_maps.get(k, k): v
        for k, v in implemented_classes.items()
        if not any(k.endswith(suffix) for suffix in ["Base", "ORM", "Table", "Link"])
        and k not in class_ignores
    }
    return implemented_classes


def report_differences(one: dict, other: dict):
    naming_one, naming_other = (
        {normalize(name): name for name in one},
        {normalize(name): name for name in other},
    )
    matching = sorted(set(naming_one) & set(naming_other))
    only_one = sorted(set(naming_one) - set(naming_other))
    only_other = sorted(set(naming_other) - set(naming_one))

    print("Classes only in the implementation:")
    print(only_one)

    print("Classes only in the definition:")
    print(only_other)

    print("Classes in both")
    print(matching)

    for clazz in matching:
        implementation = one[naming_one[clazz]]
        if "Taxonomy" in implementation["parents"]:
            continue

        print("\n", clazz)
        diffs = report_difference(one[naming_one[clazz]], other[naming_other[clazz]], clazz)
        if diffs:
            records = [dataclasses.asdict(d) for d in diffs]
            print(
                pd.DataFrame.from_records(records).loc[
                    :, ["defined_as", "implemented_as", "defined_type", "implemented_type"]
                ]
            )


@dataclasses.dataclass
class Comparison:
    normalized_name: str
    defined_as: str | None = None
    implemented_as: str | None = None
    defined_type: str | None = None
    implemented_type: str | None = None


def report_difference(one: dict, other: dict, clazz: str) -> list[Comparison]:
    implemented_properties = {
        normalize(prop): prop
        for prop in one["direct_properties"]
        if not any(prop.endswith(suffix) for suffix in property_suffix_ignores)
    }
    defined_properties = {normalize(prop["name"]): prop for prop in other["direct_properties"]}

    all_properties = set(defined_properties) | set(implemented_properties)
    property_renames = property_renames_by_class.get(clazz, {})
    # To avoid reporting a property twice, we only pick one of two definitions for properties
    # which are named differently in implementation than the conceptual model.
    all_properties = {p for p in all_properties if p not in property_renames.values()}

    property_map = []
    for property_name in all_properties:
        prop = Comparison(normalized_name=property_name)
        if implemented_as := implemented_properties.get(property_name):
            prop.implemented_as = implemented_as
            prop.implemented_type = one["properties"][implemented_as].get("type", "TYPE_UNKNOWN")

        if different_name := property_renames.get(property_name):
            property_name = different_name
        if defined_as := defined_properties.get(property_name):
            prop.defined_as = defined_as["name"]
            def_type = defined_as["range"]
            if isinstance(def_type, list) and len(def_type) == 1:
                def_type = def_type[0]
            prop.defined_type = def_type
        property_map.append(prop)

    def sort_properties(comparison):
        # we want the matched properties, then unmatched properties
        if comparison.implemented_as and comparison.defined_as:
            return ord(comparison.defined_as[0])
        if comparison.defined_as:
            return ord(comparison.defined_as[0]) + 26
        if comparison.implemented_as:
            return ord(comparison.implemented_as[0]) + 26 * 2
        raise NotImplemented

    return sorted(property_map, key=sort_properties)


if __name__ == "__main__":
    main()
