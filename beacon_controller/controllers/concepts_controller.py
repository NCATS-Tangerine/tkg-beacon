from swagger_server.models.beacon_concept import BeaconConcept
from swagger_server.models.beacon_concept_with_details import BeaconConceptWithDetails
from swagger_server.models.exact_match_response import ExactMatchResponse
from swagger_server.models.beacon_concept_detail import BeaconConceptDetail

import beacon_controller.database as db
from beacon_controller.database import Node
from beacon_controller import utils

from beacon_controller import biolink_model as blm

from collections import defaultdict

from functools import lru_cache

import yaml, ast

from typing import List

def create_details_dict(node):
    d = {}
    already_labels = ['id', 'uri', 'iri', 'name', 'category', 'symbol', 'description', 'synonym', 'clique', 'xrefs']
    for key, value in node.items():
        if key not in already_labels:
            d[key] = value
    return d

def get_concept_details(concept_id):  # noqa: E501
    """get_concept_details

    Retrieves details for a specified concepts in the system, as specified by a (url-encoded) CURIE identifier of a concept known the given knowledge source.  # noqa: E501

    :param concept_id: (url-encoded) CURIE identifier of concept of interest
    :type concept_id: str

    :rtype: BeaconConceptWithDetails
    """
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

    results = db.query(q, conceptId=concept_id)

    for result in results:
        uri = result['uri'] if result['uri'] != None else result['iri']

        clique = utils.listify(result['clique'])
        xrefs = utils.listify(result['xrefs'])
        exact_matches = clique + xrefs
        exact_matches = utils.remove_all(exact_matches, result['id'])

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
            categories=utils.standardize(result['category']),
            symbol=utils.stringify(result['symbol']),
            description=utils.stringify(result['description']),
            synonyms=utils.listify(result['synonyms']),
            exact_matches=exact_matches,
            details=details
        )
    else:
        return BeaconConceptWithDetails()


def get_concepts(keywords=None, categories=None, offset=None, size=None):  # noqa: E501
    """get_concepts

    Retrieves a list of whose concept in the beacon knowledge base with names and/or synonyms matching a set of keywords or substrings. The results returned should generally be returned in order of the quality of the match, that is, the highest ranked concepts should exactly match the most keywords, in the same order as the keywords were given. Lower quality hits with fewer keyword matches or out-of-order keyword matches, should be returned lower in the list.  # noqa: E501

    :param keywords: (Optional) array of keywords or substrings against which to match concept names and synonyms
    :type keywords: List[str]
    :param categories: (Optional) array set of concept categories - specified as Biolink name labels codes gene, pathway, etc. - to which to constrain concepts matched by the main keyword search (see [Biolink Model](https://biolink.github.io/biolink-model) for the full list of terms)
    :type categories: List[str]
    :param offset: offset (cursor position) to next batch of statements of amount &#39;size&#39; to return.
    :type offset: int
    :param size: maximum number of concept entries requested by the client; if this argument is omitted, then the query is expected to returned all the available data for the query
    :type size: int

    :rtype: List[BeaconConcept]
    """
    if keywords is None and categories is None and size is None:
        return []

    q = """
    MATCH (n)
    WHERE (
        {keywords} IS NULL OR
        ANY(keyword IN {keywords} WHERE (
            ANY(name IN n.name WHERE toLower(name) CONTAINS toLower(keyword))
        ))
    ) AND (
        {categories} IS NULL OR
        ANY(category IN {categories} WHERE (
            ANY(c IN n.category WHERE toLower(c) = toLower(category))
        ))
    )
    RETURN n
    """

    if offset is not None:
        q += f' SKIP {offset}'
    if size is not None:
        q += f' LIMIT {size}'

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


def get_exact_matches_to_concept_list(c):  # noqa: E501
    """get_exact_matches_to_concept_list

    Given an input array of [CURIE](https://www.w3.org/TR/curie/) identifiers of known exactly matched concepts [*sensa*-SKOS](http://www.w3.org/2004/02/skos/core#exactMatch), retrieves the list of [CURIE](https://www.w3.org/TR/curie/) identifiers of additional concepts that are deemed by the given knowledge source to be exact matches to one or more of the input concepts **plus** whichever concept identifiers from the input list were specifically matched to these additional concepts, thus giving the whole known set of equivalent concepts known to this particular knowledge source.  If an empty set is returned, the it can be assumed that the given knowledge source does not know of any new equivalent concepts matching the input set. The caller of this endpoint can then decide whether or not to treat  its input identifiers as its own equivalent set.  # noqa: E501

    :param c: an array set of [CURIE-encoded](https://www.w3.org/TR/curie/) identifiers of concepts thought to be exactly matching concepts, to be used in a search for additional exactly matching concepts [*sensa*-SKOS](http://www.w3.org/2004/02/skos/core#exactMatch).
    :type c: List[str]

    :rtype: List[ExactMatchResponse]
    """
    c = [utils.fix_curie(curie) for curie in c]

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
