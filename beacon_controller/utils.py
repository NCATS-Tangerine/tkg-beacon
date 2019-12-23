from functools import lru_cache
from beacon_controller import config

import logging

logger = logging.getLogger(__file__)


@lru_cache()
def prefix_map():
    """
    Returns a dictionary that maps lowercase prefixs to the case of prefixes
    as they appear in the database. Can be used to correct the case of an
    identifier.
    """
    from beacon_controller import database as db
    q="MATCH (x) RETURN  DISTINCT split(x.id, ':')[0] AS prefix"
    results = db.query(q)

    d = {}
    for result in results:
        prefix = result['prefix']

        if prefix in d:
            logger.warn('Identifier prefix {} appears in the database with multiple cases'.format(prefix))

        if isinstance(prefix, str):
            d[prefix.lower()] = prefix
        else:
            d[prefix] = prefix

    return d


def fix_curie(curie: str) -> str:
    """
    The exact matches query is case sensitive. This method can be used to ensure
    that a given curie prefix matches the case of the prefix in the database.
    """
    if curie is None or ':' not in curie:
        return ""

    prefixes = prefix_map()
    prefix, local_id = curie.split(':', 1)
    prefix = prefix.lower()

    if prefix in prefixes:
        return '{}:{}'.format(prefixes[prefix], local_id)
    else:
        return curie


def make_case_insensitive_and_inexact(strings):
    """
    Adds additional regex modifiers to make the resulting list of search terms
    case insensitive (?i) and match any part of the word (.*)
    """
    converted = list(map(lambda s: "(?i).*" + s + ".*", strings))
    return converted


def make_case_insensitive(strings):
    """
    Adds additional regex modifiers to make the resulting list of search terms
    case insensitive (?i)
    """
    converted = list(map(lambda s: "(?i)" + s, strings))
    return converted


def remove_all(original_list:list, object_to_be_removed):
    """
    Removes object_to_be_removed in list if it exists and returns list with removed items
    """
    return [i for i in original_list if i != object_to_be_removed]


def removeNonBiolinkCategories(old_categories:list):
    """
    Removes all non-Biolink compliant categories and returns the remaining list.
    If all items are removed, then returns a list containing the default, " named thing"
    """
    # categories = list(filter(isBiolinkCategory, old_categories))
    categories = [c for c in old_categories if isBiolinkCategory(c)]
    if not categories:
        #categories is empty
        categories.append(" named thing")

    return categories


def standardize(categories):
    """
    Converts categories into a list if not already
    Also removes all non-Biolink categories if filter_biolink setting is set to True
    """
    if categories is None:
        categories = []
    if not isinstance(categories, (list, set, tuple)):
        categories = [categories]
    filter_biolink = config['filter_biolink']
    if filter_biolink is True:
        categories = removeNonBiolinkCategories(categories)
    return categories


def stringify(s):
    """
    Turns s into a semicolon separated string if s is a list
    """
    if isinstance(s, (list, set)):
        s = "; ".join(s)
    return s


def listify(s):
    """
    Converts s into a list if not already. If s is None, an empty list will be returned.
    """
    if s is None:
        s = []
    elif isinstance(s, (set, tuple)):
        s = [i for i in s]
    elif not isinstance(s, list):
        s = [s]
    return s
