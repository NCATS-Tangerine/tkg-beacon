from swagger_server.models.beacon_statement import BeaconStatement

from swagger_server.models.beacon_statement_subject import BeaconStatementSubject
from swagger_server.models.beacon_statement_object import BeaconStatementObject
from swagger_server.models.beacon_statement_predicate import BeaconStatementPredicate

from swagger_server.models.beacon_statement_with_details import BeaconStatementWithDetails
from swagger_server.models.beacon_statement_citation import BeaconStatementCitation
from swagger_server.models.beacon_statement_annotation import BeaconStatementAnnotation

import beacon_controller.database as db
from beacon_controller import utils

def populate_dict(d, db_dict, prefix=None):
    for key, value in db_dict.items():
        value = utils.stringify(value)
        if prefix != None:
            d['{}_{}'.format(prefix, key)] = value
        else:
            d[key] = value

def build_evidence(publication_id):
    """
    Gets metadata for the given publication. If the publication_id is not a
    CURIE then it's assumed to be a PubMed ID.

    Note: PubMed ID's are all integers. If publication_id is neither a CURIE
    nor can it be cast to an integer, then None is returned
    """
    if isinstance(publication, str) and ':' in publication:
        prefix, local_id = publication.split(':', 1)
        if prefix.lower() == 'pmid' or prefix.lower() == 'pubmedid':
            prefix = 'pubmed'
    else:
        try:
            int(publication_id)
            prefix, local_id = 'pubmed', publication_id
        except:
            return BeaconStatementCitation(
                id=publication_id
            )

    response = requests.get(
        'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db={prefix}&id={local_id}&retmode=json'
    )

    if response.ok:
        d = response.json()
        title = d.get('title')
        journal = d.get('fulljournalname')

        if title is not None and journal is not None:
            title = f'{title}, {journal}'

        if prefix.lower() == 'pubmed':
            uri = f'https://www.ncbi.nlm.nih.gov/pubmed/{local_id}'
        else:
            uri = f'identifiers.org/{prefix}:{local_id}'

        return BeaconStatementCitation(
            id=f'{prefix}:{local_id}',
            name=title,
            uri=uri,
            date=d.get('pubdate')
        )

def get_statement_details(statement_id, keywords=None, offset=None, size=None):  # noqa: E501
    """get_statement_details

    Retrieves a details relating to a specified concept-relationship statement include &#39;is_defined_by and &#39;provided_by&#39; provenance; extended edge properties exported as tag &#x3D; value; and any associated annotations (publications, etc.)  cited as evidence for the given statement.  # noqa: E501

    :param statement_id: (url-encoded) CURIE identifier of the concept-relationship statement (\&quot;assertion\&quot;, \&quot;claim\&quot;) for which associated evidence is sought
    :type statement_id: str
    :param keywords: an array of keywords or substrings against which to  filter annotation names (e.g. publication titles).
    :type keywords: List[str]
    :param offset: offset (cursor position) to next batch of annotation entries of amount &#39;size&#39; to return.
    :type offset: int
    :param size: maximum number of evidence citation entries requested by the client; if this  argument is omitted, then the query is expected to returned all of the available annotation for this statement
    :type size: int

    :rtype: BeaconStatementWithDetails
    """
    statement_components = statement_id.split(':')

    if len(statement_components) == 2:
        q = """
        MATCH (s)-[r {id: {statement_id}}]-(o)
        RETURN s AS subject, r AS relation, o AS object
        LIMIT 1;
        """
        results = db.query(q, statement_id=statement_id)

    elif len(statement_components) == 5:
        s_prefix, s_num, edge_label, o_prefix, o_num = statement_components
        subject_id = '{}:{}'.format(s_prefix, s_num)
        object_id = '{}:{}'.format(o_prefix, o_num)
        q = """
        MATCH (s {id: {subject_id}})-[r]-(o {id: {object_id}})
        WHERE
            TOLOWER(type(r)) = TOLOWER({edge_label}) OR
            TOLOWER(r.edge_label) = TOLOWER({edge_label})
        RETURN
            s AS subject,
            r AS relation,
            o AS object
        LIMIT 1;
        """
        results = db.query(q, subject_id=subject_id, object_id=object_id, edge_label=edge_label)
    else:
        raise Exception('{} must either be a curie, or curie:edge_label:curie'.format(statement_id))

    for result in results:
        d = {}
        s = result['subject']
        r = result['relation']
        o = result['object']

        d['relationship_type'] = r.type

        populate_dict(d, s, 'subject')
        populate_dict(d, o, 'object')
        populate_dict(d, r)

        evidences = []
        if 'evidence' in r:
            for uri in r['evidence']:
                evidences.append(BeaconStatementCitation(
                    uri=utils.stringify(uri),
                ))
        if 'publications' in r:
            publications = r['publications']
            if isinstance(publications, list):
                for publication in publications:
                    evidences.append(build_evidence(publication))
            else:
                evidences.append(build_evidence(publications))

        annotations = []
        for key, value in d.items():
            annotations.append(BeaconStatementAnnotation(
                tag=key,
                value=utils.stringify(value)
            ))

        return BeaconStatementWithDetails(
            id=statement_id,
            is_defined_by=utils.stringify(r.get('is_defined_by', None)),
            provided_by=utils.stringify(r.get('provided_by', None)),
            qualifiers=r.get('qualifiers', None),
            annotation=annotations,
            evidence=evidences
        )

def get_statements(s=None, s_keywords=None, s_categories=None, edge_label=None, relation=None, t=None, t_keywords=None, t_categories=None, offset=None, size=None):  # noqa: E501
    """get_statements

    Given a constrained set of some [CURIE-encoded](https://www.w3.org/TR/curie/) &#39;s&#39; (&#39;source&#39;) concept identifiers, categories and/or keywords (to match in the concept name or description), retrieves a list of relationship statements where either the subject or the object concept matches any of the input source concepts provided.  Optionally, a set of some &#39;t&#39; (&#39;target&#39;) concept identifiers, categories and/or keywords (to match in the concept name or description) may also be given, in which case a member of the &#39;t&#39; concept set should matchthe concept opposite an &#39;s&#39; concept in the statement. That is, if the &#39;s&#39; concept matches a subject, then the &#39;t&#39; concept should match the object of a given statement (or vice versa).  # noqa: E501

    :param s: An (optional) array set of [CURIE-encoded](https://www.w3.org/TR/curie/) identifiers of &#39;source&#39; (&#39;start&#39;) concepts possibly known to the beacon. Unknown CURIES should simply be ignored (silent match failure).
    :type s: List[str]
    :param s_keywords: An (optional) array of keywords or substrings against which to filter &#39;source&#39; concept names and synonyms
    :type s_keywords: List[str]
    :param s_categories: An (optional) array set of &#39;source&#39; concept categories (specified as Biolink name labels codes gene, pathway, etc.) to which to constrain concepts matched by the main keyword search (see [Biolink Model](https://biolink.github.io/biolink-model) for the full list of codes)
    :type s_categories: List[str]
    :param edge_label: (Optional) predicate edge label against which to constrain the search for statements (&#39;edges&#39;) associated with the given query seed concept. The predicate edge_names for this parameter should be as published by the /predicates API endpoint and must be taken from the minimal predicate (&#39;slot&#39;) list of the [Biolink Model](https://biolink.github.io/biolink-model).
    :type edge_label: str
    :param relation: (Optional) predicate relation against which to constrain the search for statements (&#39;edges&#39;) associated with the given query seed concept. The predicate relations for this parameter should be as published by the /predicates API endpoint and the preferred format is a CURIE  where one exists, but strings/labels acceptable. This relation may be equivalent to the edge_label (e.g. edge_label: has_phenotype, relation: RO:0002200), or a more specific relation in cases where the source provides more granularity (e.g. edge_label: molecularly_interacts_with, relation: RO:0002447)
    :type relation: str
    :param t: An (optional) array set of [CURIE-encoded](https://www.w3.org/TR/curie/) identifiers of &#39;target&#39; (&#39;opposite&#39; or &#39;end&#39;) concepts possibly known to the beacon. Unknown CURIEs should simply be ignored (silent match failure).
    :type t: List[str]
    :param t_keywords: An (optional) array of keywords or substrings against which to filter &#39;target&#39; concept names and synonyms
    :type t_keywords: List[str]
    :param t_categories: An (optional) array set of &#39;target&#39; concept categories (specified as Biolink name labels codes gene, pathway, etc.) to which to constrain concepts matched by the main keyword search (see [Biolink Model](https://biolink.github.io/biolink-model) for the full list of codes)
    :type t_categories: List[str]
    :param offset: offset (cursor position) to next batch of statements of amount &#39;size&#39; to return.
    :type offset: int
    :param size: maximum number of concept entries requested by the client; if this argument is omitted, then the query is expected to returned all  the available data for the query
    :type size: int

    :rtype: List[BeaconStatement]
    """
    if size is None:
        size = 100

    conjuncts = []
    unwinds = []
    data = {}

    if s is not None:
        unwinds.append("[x IN {sources} | toLower(x)] AS s")
        conjuncts.append("toLower(n.id) = s")
        data['sources'] = s

    if t is not None:
        unwinds.append("[x IN {targets} | toLower(x)] AS t")
        conjuncts.append("toLower(m.id) = t")
        data['targets'] = t

    if s_keywords is not None:
        unwinds.append("[x IN {s_keywords} | toLower(x)] AS s_keyword")
        disjuncts = [
            "toLower(n.name) CONTAINS s_keyword",
            "ANY(syn IN n.synonym WHERE toLower(syn) CONTAINS s_keyword)"
        ]
        conjuncts.append(" OR ".join(disjuncts))
        # conjuncts.append("toLower(n.name) CONTAINS s_keyword OR ANY(synonym IN n.synonym WHERE toLower(synonym) CONTAINS s_keyword)")
        data['s_keywords'] = s_keywords

    if t_keywords is not None:
        unwinds.append("[x IN {t_keywords} | toLower(x)] AS t_keyword")
        disjuncts = [
            "toLower(m.name) CONTAINS t_keyword",
            "ANY(syn IN m.synonym WHERE toLower(syn) CONTAINS t_keyword)"
        ]
        conjuncts.append(" OR ".join(disjuncts))
        # conjuncts.append("ANY(keyword in {t_keywords} WHERE keyword CONTAINS toLower(m.name))")
        # conjuncts.append("toLower(m.name) CONTAINS t_keyword OR ANY(synonym IN m.synonym WHERE toLower(synonym) CONTAINS t_keyword)")
        data['t_keywords'] = t_keywords

    if edge_label is not None:
        conjuncts.append("type(r) = {edge_label}")
        data['edge_label'] = edge_label

    if relation is not None:
        conjuncts.append("r.relation = {relation}")
        data['relation'] = relation

    if s_categories is not None:
        unwinds.append("[x IN {s_categories} | toLower(x)] AS s_category")
        conjuncts.append("s_category IN labels(n))")
        data['s_categories'] = s_categories

    if t_categories is not None:
        unwinds.append("[x IN {t_categories} | toLower(x)] AS t_category")
        conjuncts.append("t_category IN labels(m)")
        data['t_categories'] = t_categories

    q = "MATCH (n)-[r]->(m)"

    if unwinds != []:
        q = "UNWIND " + ' UNWIND '.join(unwinds) + " " + q

    if conjuncts != []:
        q = q + " WHERE (" + ') AND ('.join(conjuncts) + ")"

    q += """
    RETURN
        n AS subject,
        m AS object,
        type(r) AS edge_type,
        r.edge_label AS edge_label,
        r.relation AS relation,
        r.negated AS negated,
        r.id AS statement_id
    """

    if isinstance(offset, int) and offset >= 0:
        q += f' SKIP {offset}'
    if isinstance(size, int) and size >= 1:
        q += f' LIMIT {size}'

    results = db.query(
        q,
        **data
    )

    statements = []

    for result in results:
        s, o = result['subject'], result['object']

        s_categories = utils.standardize(s['category'])
        o_categories = utils.standardize(o['category'])

        if result['edge_label'] != None:
            edge_label = utils.stringify(result['edge_label'])
        else:
            edge_label = utils.stringify(result['edge_type'])

        beacon_subject = BeaconStatementSubject(
            id=s['id'],
            name=utils.stringify(s['name']),
            categories=utils.standardize(s['category'])
        )

        beacon_predicate = BeaconStatementPredicate(
            edge_label=edge_label,
            relation=utils.stringify(result['relation']),
            negated=bool(result['negated'])
        )

        beacon_object = BeaconStatementObject(
            id=o['id'],
            name=utils.stringify(o['name']),
            categories=utils.standardize(o['category'])
        )

        statement_id = result['statement_id']
        if statement_id == None:
            statement_id = '{}:{}:{}'.format(s['id'], edge_label, o['id'])

        statements.append(BeaconStatement(
            id=statement_id,
            subject=beacon_subject,
            predicate=beacon_predicate,
            object=beacon_object
        ))

    return statements
