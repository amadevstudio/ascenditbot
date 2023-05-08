def get_all_level_values(in_hash):
    values = []
    child_hashes = []
    for v in in_hash.values():
        (child_hashes if isinstance(v, dict) else values).append(v)

    while len(child_hashes) > 0:
        curr_hash = child_hashes.pop()
        for v in curr_hash.values():
            (child_hashes if isinstance(v, dict) else values).append(v)

    return values
