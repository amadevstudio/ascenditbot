from typing import TypedDict


class ModelWithId(TypedDict, total=False):
    id: int


def hashed_by_id(models: list[dict]) -> dict[int, dict]:
    result = {}
    for model in models:
        result[model['id']] = model
    return result
