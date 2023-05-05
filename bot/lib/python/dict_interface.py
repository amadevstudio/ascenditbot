from typing import TypedDict, Type


def validate_structure(struct, conf):
    if isinstance(struct, dict) and isinstance(conf, dict):
        # struct is a dict of types or other dicts
        return all(k in conf and validate_structure(struct[k], conf[k]) for k in struct)
    if isinstance(struct, list) and isinstance(conf, list):
        # struct is list in the form [type or dict]
        return all(validate_structure(struct[0], c) for c in conf)
    elif isinstance(conf, type):
        # struct is the type of conf
        return isinstance(struct, conf)
    elif isinstance(conf, tuple):
        return struct in conf or type(struct) in conf
    else:
        # struct is neither a dict, nor list, not type
        return False


def validate_typed_dict_interface(dictionary: dict, interface: Type[TypedDict]):
    return isinstance(dictionary, dict) and all(key in interface.__annotations__ for key in dictionary.keys())
