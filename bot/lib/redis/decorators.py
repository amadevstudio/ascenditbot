def convert_bytes_to_strings(func):
    def _wrap(*args, **kwargs):
        result = func(*args, **kwargs)

        if isinstance(result, list):
            unbyted = [v.decode("UTF-8") for v in result]
        elif isinstance(result, bytes):
            unbyted = result.decode("UTF-8")
        else:
            unbyted = result

        return unbyted

    return _wrap
