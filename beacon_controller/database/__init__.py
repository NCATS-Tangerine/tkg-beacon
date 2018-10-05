from . import config
from .model import Node, Edge

from neomodel import db

def query(q, inflator=None, **kwargs):
    results, meta = db.cypher_query(q, kwargs)

    if inflator != None:
        return [inflator.inflate(row[0]) for row in results]
    else:
        rows = []
        for result in results:
            row = {}
            for i, key in enumerate(meta):
                row[key] = result[i]
            rows.append(row)
        return rows
