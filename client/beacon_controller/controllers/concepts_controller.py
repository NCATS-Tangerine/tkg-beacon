from swagger_server.models.beacon_concept import BeaconConcept
from swagger_server.models.beacon_concept_with_details import BeaconConceptWithDetails
from swagger_server.models.exact_match_response import ExactMatchResponse
from swagger_server.models.beacon_concept_detail import BeaconConceptDetail

import beacon_controller.database as db
from beacon_controller.database import Node
from beacon_controller import utils

import yaml
import ast

def create_details_dict(node):
    d = {}
    already_labels = ['id', 'uri', 'iri', 'name', 'category', 'symbol', 'description', 'synonym', 'clique', 'xrefs']
    for key, value in node.items():
        if key not in already_labels:
            d[key] = value
    return d

def get_concept_details(conceptId):
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
        n.xrefs AS xrefs,
        n AS node
    LIMIT 1
    """

    results = db.query(q, conceptId=conceptId)

    for result in results:
        uri = result['uri'] if result['uri'] != None else result['iri']
        synonyms = utils.listify(result['synonyms'])

        clique = utils.listify(result['clique'])
        xrefs = utils.listify(result['xrefs'])

        exact_matches = clique + xrefs

        exact_matches = utils.remove_all(exact_matches, result['id'])

        categories = utils.standardize(result['category'])

        details_dict = create_details_dict(result['node'])
        details = []
        for key, value in details_dict.items():
            details.append(BeaconConceptDetail(
                tag=key,
                value=utils.stringify(value)
            ))

        return BeaconConceptWithDetails(
            id=result['id'],
            uri=utils.stringify(uri),
            name=utils.stringify(result['name']),
            categories=categories,
            symbol=utils.stringify(result['symbol']),
            description=utils.stringify(result['description']),
            synonyms=synonyms,
            exact_matches=exact_matches,
            details=details
        )

def get_concepts(keywords, categories=None, size=None):
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

def get_exact_matches_to_concept_list(c):
    q = """
    MATCH (n) WHERE
        ANY(id IN {id_list} WHERE TOLOWER(n.id) = TOLOWER(id))
    RETURN
        n.id AS id,
        n.xrefs AS xrefs,
        n.clique AS clique
    """

    results = db.query(q, id_list=c)
    exact_match_responses = []
    for result in results:
        c.remove(result['id'])

        exact_matches = []

        if isinstance(result['xrefs'], (list, tuple, set)):
            exact_matches += result['xrefs']

        if isinstance(result['clique'], (list, tuple, set)):
            exact_matches += result['clique']

        exact_matches = utils.remove_all(exact_matches, result['id'])

        exact_match_responses.append(ExactMatchResponse(
            id=result['id'],
            within_domain=True,
            has_exact_matches=list(set(exact_matches))
        ))

    for curie_id in c:
        exact_match_responses.append(ExactMatchResponse(
            id=curie_id,
            within_domain=False,
            has_exact_matches=[]
        ))

    return exact_match_responses
