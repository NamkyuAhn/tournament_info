import json


def decode_tournament_json_fields(data):
    """Decode the JSON strings embedded in tournament form submissions."""
    for field in ("poker_tournament", "prize_structure"):
        if field in data:
            data[field] = json.loads(data[field])
    return data
