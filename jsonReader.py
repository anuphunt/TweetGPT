import json


def read(filename):
    with open(filename) as f:
        data = json.load(f)
    return data
