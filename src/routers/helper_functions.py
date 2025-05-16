import routers
from database.model.concept.concept import AIoDConcept
from database.model.helper_functions import non_abstract_subclasses


def get_all_read_classes() -> dict[str, AIoDConcept]:
    """Returns a list of all schema types and a reference to their definition."""
    available_schemas: list[AIoDConcept] = list(non_abstract_subclasses(AIoDConcept))
    classes_dict = {clz.__tablename__: clz for clz in available_schemas if clz.__tablename__}
    resrouters = {
        route.resource_name: route
        for route in routers.resource_routers.router_list  # type: ignore
    }
    return {
        name: resrouters[name].resource_class_read
        for name in classes_dict
        if name not in ["testresource", "test_object"]
    }


def get_all_asset_schemas():
    return [
        {"$ref": f"#/components/schemas/{clz.__name__}"} for clz in get_all_read_classes().values()
    ]
