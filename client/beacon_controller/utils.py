import os, yaml, threading

import beacon_controller as ctrl
from beacon_ontology import getEntityByName
from beacon_ontology.biolink_class import BiolinkClass

__sample_name = 'config.sample.yaml'

__config_dict = None

def start_new_thread(method, args):
    thread = threading.Thread(target=method, args=args)
    thread.daemon = True
    thread.start()

def initiate_metadata_cache():
    """
    The metadata methods are very slow, but they automatically cache their
    results. So we will call them on new threads to initiate the cache.
    """
    start_new_thread(ctrl.get_concept_categories, ())
    start_new_thread(ctrl.get_knowledge_map, ())
    start_new_thread(ctrl.get_predicates, ())

def load_config(silent=True):
    """
    Walks backwards from __file__ to find config.yaml, loads and returns as a
    dictionary.

    Note: traverses up whole file system if config.yaml is not found, but this
          doesn't appear to be a costly opperation.

    source: https://www.programcreek.com/python/example/3198/yaml.safe_load
    """

    global __config_dict

    if __config_dict is not None:
        return __config_dict

    config = None
    f = __file__
    while config is None:
        d = os.path.dirname(f)
        path = os.path.join(d, 'config.yaml')

        if not silent:
            print('Searching for config.yaml in:', path)

        if os.path.isfile(path):
            config = path
            break
        elif f == d:
            break

        f = d

    if not config:
        raise Exception('Could not find config.yaml in any parent directory of {}, try copying and renaming {} in projects root directory'.format(__file__, __sample_name))

    __config_dict = yaml.safe_load(open(config).read())

    return __config_dict

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
    Removes first of string in list if it exists and returns list with removed items
    """
    return [i for i in original_list if i != object_to_be_removed]

def removeNonBiolinkCategories(old_categories:list):
    """
    Removes all non-Biolink compliant categories and returns the remaining list.
    If all items are removed, then returns a list containing the default, "named thing"
    """
    # categories = list(filter(isBiolinkCategory, old_categories))
    categories = [c for c in old_categories if isBiolinkCategory(c)]
    if not categories:
        #categories is empty
        categories.append("named thing")
    
    return categories

def isBiolinkCategory(c):
    test = getEntityByName(c)
    return test != None and isinstance(test, BiolinkClass)

def standardize(categories):
    """
    Converts categories into a list if not already
    Also removes all non-Biolink categories if filter_biolink setting is set to True
    """
    if categories is None:
        categories = []
    if not isinstance(categories, (list, set, tuple)):
        categories = [categories]
    filter_biolink = load_config()['general']['filter_biolink']
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