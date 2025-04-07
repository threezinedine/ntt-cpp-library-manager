from typing import Optional, Dict, Any
from datetime import datetime


def dict_to_dataclass(data_dict: Dict[str, Any], data_class: type) -> Any:
    """
    Convert a dictionary to a dataclass object.
    Handles nested dataclasses and basic type conversions.

    Args:
        data_dict: Dictionary containing the data
        data_class: The target dataclass type

    Returns:
        An instance of the dataclass
    """
    field_types = {
        field.name: field.type for field in data_class.__dataclass_fields__.values()
    }

    kwargs = {}
    for field_name, field_value in data_dict.items():
        if field_name not in field_types:
            continue

        field_type = field_types[field_name]

        # Handle nested dataclass
        if hasattr(field_type, "__dataclass_fields__"):
            if field_value is not None:
                kwargs[field_name] = dict_to_dataclass(field_value, field_type)
            continue

        # Handle datetime
        if field_type == datetime and isinstance(field_value, str):
            kwargs[field_name] = datetime.fromisoformat(field_value)
            continue

        # Handle Optional types
        if hasattr(field_type, "__origin__") and field_type.__origin__ is Optional:
            if field_value is None:
                kwargs[field_name] = None
                continue
            field_type = field_type.__args__[0]

        # Handle lists
        if hasattr(field_type, "__origin__") and field_type.__origin__ is list:
            if not field_value:
                kwargs[field_name] = []
            else:
                item_type = field_type.__args__[0]
                if hasattr(item_type, "__dataclass_fields__"):
                    kwargs[field_name] = [
                        dict_to_dataclass(item, item_type) for item in field_value
                    ]
                else:
                    kwargs[field_name] = field_value
            continue

        kwargs[field_name] = field_value

    return data_class(**kwargs)
