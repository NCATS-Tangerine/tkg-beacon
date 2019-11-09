from swagger_server.models.beacon_concept_category import BeaconConceptCategory
from swagger_server.models.beacon_knowledge_map_statement import BeaconKnowledgeMapStatement
from swagger_server.models.beacon_knowledge_map_subject import BeaconKnowledgeMapSubject
from swagger_server.models.beacon_knowledge_map_predicate import BeaconKnowledgeMapPredicate
from swagger_server.models.beacon_knowledge_map_object import BeaconKnowledgeMapObject
from swagger_server.models.beacon_predicate import BeaconPredicate
from swagger_server.models.namespace import Namespace
from swagger_server.models.local_namespace import LocalNamespace

from cachetools.func import ttl_cache

import beacon_controller.database as db
from beacon_controller.database import Node
from beacon_controller import utils, config
from beacon_controller import biolink_model as blm

import data
import pandas as pd
import os

from collections import defaultdict

edge_path = os.path.join(data.path, config['beacon_name'], 'edge_summary.txt')
node_path = os.path.join(data.path, config['beacon_name'], 'node_summary.txt')


__time_to_live_in_seconds = 604800

def camel_case(s:str) -> str:
    return ''.join(w.title() for w in s.replace('_', ' ').split(' '))

@ttl_cache(ttl=__time_to_live_in_seconds)
def get_concept_categories():  # noqa: E501
    """get_concept_categories

    Get a list of concept categories and number of their concept instances documented by the knowledge source. These types should be mapped onto the Translator-endorsed Biolink Model concept type classes with local types, explicitly added as mappings to the Biolink Model YAML file. A frequency of -1 indicates the category can exist, but the count is unknown.  # noqa: E501


    :rtype: List[BeaconConceptCategory]
    """
    rows = pd.read_csv(node_path, sep='|').to_dict(orient='records')

    category_dict = defaultdict(lambda: 0)
    for row in rows:
        category_dict[row['category']] += row['frequency']
    sorted_results = sorted(category_dict.items(), key=lambda k: k[1], reverse=True)

    categories = []
    for category, frequency in sorted_results:
        c = blm.get_class(category)
        if c is not None:
            categories.append(BeaconConceptCategory(
                frequency=frequency,
                category=category,
                local_category=category,
                description=c.description
            ))
        else:
            c = blm.get_class(blm.DEFAULT_CATEGORY)
            categories.append(BeaconConceptCategory(
                frequency=frequency,
                category=blm.DEFAULT_CATEGORY,
                local_category=category,
                description=c.description
            ))

    return categories

@ttl_cache(ttl=__time_to_live_in_seconds)
def get_knowledge_map():  # noqa: E501
    """get_knowledge_map

    Get a high level knowledge map of the all the beacons by subject semantic type, predicate and semantic object type  # noqa: E501


    :rtype: List[BeaconKnowledgeMapStatement]
    """
    rows = pd.read_csv(edge_path, sep='|').to_dict(orient='records')

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
def get_predicates():  # noqa: E501
    """get_predicates

    Get a list of predicates used in statements issued by the knowledge source  # noqa: E501


    :rtype: List[BeaconPredicate]
    """
    rows = pd.read_csv(edge_path, sep='|').to_dict(orient='records')

    d = defaultdict(lambda: 0)

    for row in rows:
        edge_type = row['edge_type']
        relation = row['relation']
        d[f'{edge_type}|{relation}'] += row['frequency']

    results = sorted(d.items(), key=lambda t: t[1], reverse=True)

    predicates = []

    for key, frequency in results:
        edge_type, relation = key.split('|')

        slot = blm.get_slot(edge_type)

        if slot is not None:
            predicates.append(BeaconPredicate(
                edge_label=edge_type,
                relation=relation,
                frequency=frequency,
                description=slot.description
            ))
        else:
            slot = blm.get_slot(blm.DEFAULT_EDGE_LABEL)
            if relation is None:
                relation = edge_type
            predicates.append(BeaconPredicate(
                edge_label=blm.DEFAULT_EDGE_LABEL,
                relation=relation,
                frequency=frequency,
                description=slot.description
            ))

    return predicates

from prefixcommons.curie_util import default_curie_maps as cmaps

def prefix_to_uri(prefix):
    """
    Pulls the default curie map from prefixcommons and gets the uri from it
    """
    prefix = prefix.upper()

    for cmap in cmaps:
        for key, value in cmap.items():
            if prefix.lower() == key.lower():
                return value
    else:
        return None


@ttl_cache(ttl=__time_to_live_in_seconds)
def get_namespaces():  # noqa: E501
    """get_namespaces
    Get a list of namespace (curie prefixes) mappings that this beacon can perform with its /exactmatches endpoint  # noqa: E501
    :rtype: List[LocalNamespace]
    """
    q = """
    MATCH (n)
    WITH
        split(n.id, ":")[0] AS prefix,
        FILTER(x IN n.xrefs WHERE x <> n.id) AS xrefs,
        FILTER(x IN n.clique WHERE x <> n.id) AS clique
    WITH
        prefix AS prefix,
        EXTRACT(id IN xrefs | split(id, ":")[0]) AS xref_prefixes,
        EXTRACT(id IN clique | split(id, ":")[0]) AS clique_prefixes
    UNWIND
        COALESCE(xref_prefixes, []) + COALESCE(clique_prefixes, []) As p
    RETURN DISTINCT prefix AS local_prefix, COLLECT(DISTINCT p) AS clique_prefixes, COUNT(*) AS frequency;
    """

    results = db.query(q)

    local_namespaces = []

    for result in results:
        local_prefix = result.get('local_prefix')
        clique_prefixes = result.get('clique_prefixes')
        frequency = result.get('frequency')

        namespaces = []
        for prefix in clique_prefixes:
            namespaces.append(Namespace(
                prefix=prefix,
                uri=prefix_to_uri(prefix)
            ))

        local_namespaces.append(LocalNamespace(
            local_prefix=local_prefix,
            clique_mappings=namespaces,
            frequency=frequency,
            uri=prefix_to_uri(local_prefix),
        ))

    return local_namespaces
