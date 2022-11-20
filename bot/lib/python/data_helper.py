def get_all_level_values(in_hash):
    values = []
    child_hashes = []
    for v in in_hash.values():
        (child_hashes if isinstance(v, dict) else values).append(v)

    for h in child_hashes:
        values += get_all_level_values(h)

    return values
