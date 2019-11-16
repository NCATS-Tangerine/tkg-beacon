"""
Utility module for handling conversion between IRI's and CURIE's.

Maintains a memory of URI prefixes that have been mapped onto CURIE prefixes.
"""

from prefixcommons import contract_uri
from prefixcommons.curie_util import default_curie_maps

from collections import defaultdict

from typing import List

from tinydb import TinyDB, Query

db = TinyDB('db.json')

Record = Query()

default_curie_maps += [{
    'OMIM' : 'http://omim.org/entry/'
}]

uri_prefixes_dict = defaultdict(list)
curie_prefixes_dict = defaultdict(list)

def _curie(uri:str):
    """
    Attempts to contract a URI. If unable to, returns the origional URI. If
    many contractions are available, chooses the shortest.
    """
    curies = contract_uri(uri)

    if len(curies) == 0:
        return uri
    elif len(curies) == 1:
        return curies[0]
    else:
        curies.sort(key=len)
        return curies[0]

def curie(uri:str):
    c = _curie(uri)

    if c == uri:
        return c

    curie_prefix, id = c.split(':')

    uri_prefix, _ = uri.split(id)

    uri_prefixes_dict[uri_prefix].append(curie_prefix)
    curie_prefixes_dict[curie_prefix].append(uri_prefix)

    return c

def uri_prefixes(curie_prefix:str) -> list:
    """
    Returns a list of URI prefixes that have been mapped onto the given CURIE
    throughout the duration of the application
    """
    if ':' in curie_prefix:
        curie_prefix, _ = curie_prefix.split(':')
    return curie_prefixes_dict[curie_prefix]

def expand(curies:List[str]) -> List[str]:
    if curies is None:
        []
    for curie in curies:
        prefix, identifier = curie.split(':')
        uri_prefixes_list = uri_prefixes(prefix)
        return [f'{p}:{identifier}' for p in uri_prefixes_list]
