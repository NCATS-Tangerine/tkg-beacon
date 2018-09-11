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

from beacon_controller import config, basepath
import pandas as pd
import os

from collections import defaultdict

__time_to_live_in_seconds = 604800

edge_summary = os.path.join(basepath, 'data', config['client']['kgx_name'], 'edge_summary.txt')
node_summary = os.path.join(basepath, 'data', config['client']['kgx_name'], 'node_summary.txt')

def camel_case(s:str) -> str:
    return ''.join(w.title() for w in s.replace('_', ' ').split(' '))

@ttl_cache(ttl=__time_to_live_in_seconds)
def get_concept_categories():
    rows = pd.read_csv(node_summary, sep='|').to_dict(orient='records')

    category_dict = defaultdict(lambda: 0)
    for row in rows:
        category_dict[row['category']] += row['frequency']
    sorted_results = sorted(category_dict.items(), key=lambda k: k[1], reverse=True)

    categories = []
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
    rows = pd.read_csv(edge_summary, sep='|').to_dict(orient='records')

    frequency = defaultdict(lambda: 0)
    subject_prefixes = defaultdict(set)
    object_prefixes = defaultdict(set)
    for row in rows:
        # |subject_category|subject_prefix|edge_type|object_category|object_prefix|provided_by|frequency
        triple = (row['subject_category'], row['edge_type'], row['object_category'])
        frequency[triple] += row['frequency']
        subject_prefixes[triple].add(row['subject_prefix'])
        object_prefixes[triple].add(row['object_prefix'])

    maps = []
    for key, fq in frequency.items():
        subject_category, edge_type, object_category = key
        subject_prefix = subject_prefixes[key]
        object_prefix = object_prefixes[key]

        o = BeaconKnowledgeMapObject(
            category=object_category,
            prefixes=list(object_prefix)
        )

        p = BeaconKnowledgeMapPredicate(
            edge_label=edge_type
            # TODO: gather negated in KGX summary?
            # negated=None
        )

        s = BeaconKnowledgeMapSubject(
            category=subject_category,
            prefixes=list(subject_prefix)
        )

        maps.append(BeaconKnowledgeMapStatement(
            subject=s,
            predicate=p,
            object=o,
            frequency=fq
        ))

    maps = sorted(maps, key=lambda k: k.frequency, reverse=True)

    return maps

@ttl_cache(ttl=__time_to_live_in_seconds)
def get_predicates():
    rows = pd.read_csv(edge_summary, sep='|').to_dict(orient='records')

    d = defaultdict(lambda: 0)

    for row in rows:
        d[row['edge_type']] += row['frequency']

    results = sorted(d.items(), key=lambda t: t[1], reverse=True)

    predicates = []

    for edge_type, frequency in results:
        predicates.append(BeaconPredicate(
            edge_label=edge_type,
            frequency=frequency
        ))

    return predicates
