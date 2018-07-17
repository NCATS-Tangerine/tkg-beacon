from swagger_server.models.beacon_concept_category import BeaconConceptCategory
from swagger_server.models.beacon_knowledge_map_statement import BeaconKnowledgeMapStatement
from swagger_server.models.beacon_knowledge_map_subject import BeaconKnowledgeMapSubject
from swagger_server.models.beacon_knowledge_map_predicate import BeaconKnowledgeMapPredicate
from swagger_server.models.beacon_knowledge_map_object import BeaconKnowledgeMapObject
from swagger_server.models.beacon_predicate import BeaconPredicate

from cachetools.func import ttl_cache

import beacon_controller.database as db
from beacon_controller.database import Node
from beacon_controller import utils

from collections import defaultdict

__time_to_live_in_seconds = 604800

def camel_case(s:str) -> str:
    return ''.join(w.title() for w in s.replace('_', ' ').split(' '))

@ttl_cache(ttl=__time_to_live_in_seconds)
def get_concept_categories():
    q = 'MATCH (x) RETURN DISTINCT x.category AS category, COUNT(*) AS frequency;'
    results = db.query(q)

    category_dict = {}
    for result in results:
        categories = utils.standardize(result['category'])
        for c in categories:
            if c in category_dict:
                category_dict[c] += result['frequency']
            else: 
                category_dict[c] = result['frequency']
    
    categories = []
    sorted_results = sorted(category_dict.items(), key=lambda k: k[1], reverse=True)
    for category, frequency in sorted_results:
        uri = 'http://bioentity.io/vocab/{}'.format(camel_case(category))
        identifier = 'BLM:{}'.format(camel_case(category))
        categories.append(BeaconConceptCategory(
            id=identifier,
            uri=uri,
            frequency=frequency,
            category=category
        ))

    return categories

def equal_dicts(d1:dict, d2:dict, ignore_keys:list) -> bool:
    """
    source: https://stackoverflow.com/a/10480904
    """
    if not isinstance(ignore_keys, (list, set, tuple)):
        ignore_keys = [ignore_keys]

    d1 = {k : v for k, v in d1.items() if k not in ignore_keys}
    d2 = {k : v for k, v in d2.items() if k not in ignore_keys}
    return d1 == d2

def eq(d1, d2):
    return equal_dicts(d1, d2, 'frequency')

def split_up_categories(results):
    def split_up_by_key(dicts, key):
        new_dict = []
        for old_dict in dicts:
            for c in utils.standardize(old_dict[key]):
                d = dict(old_dict)
                d[key] = c
                new_dict.append(d)
        return new_dict

    results = split_up_by_key(results, 'subject_category')
    return split_up_by_key(results, 'object_category')

def add_up_duplicates(results):
    for a in results:
        gen = (i for i, b in enumerate(results) if a is not b and equal_dicts(a, b, 'frequency'))
        i = next(gen, None)
        while i != None:
            a['frequency'] += results[i]['frequency']
            del results[i]
            i = next(gen, None)

@ttl_cache(ttl=__time_to_live_in_seconds)
def get_knowledge_map():
    q = """
    MATCH (x)-[r]->(y)
    RETURN DISTINCT
        x.category AS subject_category,
        type(r) AS edge_label,
        r.relation AS relation,
        y.category AS object_category,
        r.negated AS negated,
        COUNT(*) AS frequency;
    """

    results = db.query(q)
    results = split_up_categories(results)
    add_up_duplicates(results)
    results = sorted(results, key=lambda k: k['frequency'], reverse=True)

    results = [d for d in results if not isinstance(d['subject_category'], list) and not isinstance(d['object_category'], list)]

    maps = []
    for result in results:
        o = BeaconKnowledgeMapObject(
            category=result['object_category'],
            prefixes=[]
        )

        p = BeaconKnowledgeMapPredicate(
            edge_label=result['edge_label'],
            relation=result['relation'],
            negated=bool(result['negated'])
        )

        s = BeaconKnowledgeMapSubject(
            category=result['subject_category'],
            prefixes=[]
        )

        maps.append(BeaconKnowledgeMapStatement(
            subject=s,
            predicate=p,
            object=o,
            frequency=result['frequency']
        ))

    return maps

@ttl_cache(ttl=__time_to_live_in_seconds)
def get_predicates():
    q = """
    MATCH (x)-[r]->(y)
    RETURN DISTINCT type(r) AS predicate, r.relation AS relation, COUNT(*) AS frequency;
    """

    results = db.query(q)

    results = sorted(results, key=lambda k: k['frequency'], reverse=True)

    predicates = []

    for result in results:
        predicates.append(BeaconPredicate(
            id=result['relation'],
            edge_label=result['predicate'],
            frequency=result['frequency']
        ))

    return predicates
