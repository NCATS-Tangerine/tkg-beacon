from swagger_server.models.beacon_concept import BeaconConcept
from swagger_server.models.beacon_concept_with_details import BeaconConceptWithDetails
from swagger_server.models.exact_match_response import ExactMatchResponse

import beacon_controller.database as db
from beacon_controller.database import Node
from beacon_controller import utils

from collections import defaultdict

import yaml, ast

from typing import List

def get_concept_details(conceptId:str) -> BeaconConceptWithDetails:
    q = """
    MATCH (n) WHERE LOWER(n.id)=LOWER({conceptId})
    RETURN
        n.id AS id,
        n.uri AS uri,
        n.iri AS iri,
        n.name AS name,
        n.category AS category,
        n.symbol AS symbol,
        n.description AS description,
        n.synonym AS synonyms,
        n.clique AS clique,
        n.xrefs AS xrefs
    LIMIT 1
    """

    results = db.query(q, conceptId=conceptId)

    for result in results:
        uri = result['uri'] if result['uri'] != None else result['iri']
        synonyms = result['synonyms'] if result['synonyms'] != None else []

        clique = result['clique'] if result['clique'] != None else []
        xrefs = result['xrefs'] if result['xrefs'] != None else []

        exact_matches = list(set(clique + xrefs))

        exact_matches = utils.remove_all(exact_matches, result['id'])

        categories = utils.standardize(result['category'])

        return BeaconConceptWithDetails(
            id=result['id'],
            uri=uri,
            name=result['name'],
            categories=categories,
            symbol=result['symbol'],
            description=result['description'],
            synonyms=result['synonyms'],
            exact_matches=exact_matches
        )

def get_concepts(keywords:List[str], categories:List[str]=None, size:int=None) -> BeaconConcept:
    size = size if size is not None and size > 0 else 100
    categories = categories if categories is not None else []

    q = """
    MATCH (n)
    WHERE
        (ANY (keyword IN {keywords} WHERE
            (ANY (name IN n.name WHERE LOWER(name) CONTAINS LOWER(keyword))))) AND
        (SIZE({categories}) = 0 OR
            ANY (category IN {categories} WHERE
            (ANY (name IN n.category WHERE LOWER(name) = LOWER(category)))))
    RETURN n
    LIMIT {limit}
    """

    nodes = db.query(q, Node, keywords=keywords, categories=categories, limit=size)

    concepts = []

    for node in nodes:
        if all(len(category) == 1 for category in node.category):
            node.category = [''.join(node.category)]
        categories = utils.standardize(node.category)
        concept = BeaconConcept(
            id=node.curie,
            name=node.name,
            categories=categories,
            description=node.description
        )

        concepts.append(concept)

    return concepts

def get_exact_matches_to_concept_list(c:List[str]) -> List[ExactMatchResponse]:
    """
    Gets a set of *case sensitive* exact matches for the given list of curie
    identifiers. Making the Cypher query case insensitive results in significantly
    slower performance. It is assumed that the database uses capital characters
    for its identifiers. E.g., HP:0010313 and not hp:0010313.

    :param c: an array set of [CURIE-encoded](https://www.w3.org/TR/curie/) identifiers of concepts thought to be exactly matching concepts, to be used in a search for additional exactly matching concepts [*sensa*-SKOS](http://www.w3.org/2004/02/skos/core#exactMatch).
    :type c: List[str]

    :rtype: List[ExactMatchResponse]
    """
    # ["HP:0010313", "DOID:3459", "HP:0009800", "MONDO:0004989"]

    # "CCPSS:0033438","EFO:0001359","OBO:KEGG_04940","OBO:COHD_201254",
    # "DOID:9744","NCIT:C2986","CHV:0000047456","OBO:SCTID_46635009","MESH:D003922"

    q = """
    UNWIND {id_list} AS input_id
    MATCH (n) WHERE
        n.id = input_id OR
        input_id IN n.xrefs OR
        input_id IN n.clique
    RETURN
    	input_id AS input_id,
        n.id AS match_id,
        n.xrefs AS xrefs,
        n.clique AS clique;
    """

    results = db.query(q, id_list=c)

    exactmatch_dict = defaultdict(set)

    for result in results:
        input_id = result.get('input_id')
        match_id = result.get('match_id')
        clique = result.get('clique')
        xrefs = result.get('xrefs')

        if isinstance(match_id, str):
            exactmatch_dict[input_id].add(match_id)

        if isinstance(clique, (list, tuple, set)):
            exactmatch_dict[input_id].update(clique)

        if isinstance(xrefs, (list, tuple, set)):
            exactmatch_dict[input_id].update(xrefs)

    exactmatch_responses = []

    for curie in c:
        if curie in exactmatch_dict:
            exactmatch_responses.append(ExactMatchResponse(
                id=curie,
                within_domain=True,
                has_exact_matches=list(exactmatch_dict[curie])
            ))
        else:
            exactmatch_responses.append(ExactMatchResponse(
                id=curie,
                within_domain=False,
                has_exact_matches=[]
            ))

    return exactmatch_responses
