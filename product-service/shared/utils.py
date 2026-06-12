def compact_dict(data: dict) -> dict:
    return {key: value for key, value in data.items() if value is not None}
