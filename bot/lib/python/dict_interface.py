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


def validate_typed_dict_interface(dictionary: dict, interface: Type[TypedDict], total=False) -> bool:
    dict_is_dict = isinstance(dictionary, dict)
    base_check = all(key in interface.__annotations__ for key in dictionary.keys())
    if total:
        total_check = all(key in dictionary.keys() for key in interface.__annotations__)
    else:
        total_check = True

    return dict_is_dict and base_check and total_check
