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
        if prefix != None:
            d['{}_{}'.format(prefix, key)] = value
        else:
            d[key] = value

def get_statement_details(statementId, keywords=None, size=None):
    statement_components = statementId.split(':')

    if len(statement_components) == 2:
        q = """
        MATCH (s)-[r {id: {statement_id}}]-(o)
        RETURN s AS subject, r AS relation, o AS object
        LIMIT 1;
        """
        results = db.query(q, statement_id=statementId)

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
        raise Exception('{} must either be a curie, or curie:edge_label:curie'.format(statementId))

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
                    uri=uri,
                ))
        if 'publications' in r:
            for pm_uri in r['publications']:
                evidences.append(BeaconStatementCitation(
                    uri=pm_uri
                ))

        annotations = []
        for key, value in d.items():
            annotations.append(BeaconStatementAnnotation(
                tag=key,
                value=utils.stringify(value)
            ))

        return BeaconStatementWithDetails(
            id=statementId,
            is_defined_by=utils.stringify(r.get('is_defined_by', None)),
            provided_by=utils.stringify(r.get('provided_by', None)),
            qualifiers=r.get('qualifiers', None),
            annotation=annotations,
            evidence=evidences
        )

def get_statements(s, edge_label=None, relation=None, t=None, keywords=None, categories=None, size=None):
    size = 100 if size == None or size < 1 else size

    q = """
    MATCH (n)-[r]-(m)
    WHERE
        ANY(id IN {sources} WHERE TOLOWER(n.id) = TOLOWER(id)) AND
        ({targets} IS NULL OR ANY(id IN {targets} WHERE TOLOWER(m.id) = TOLOWER(id))) AND
        ({edge_label} IS NULL OR type(r) = {edge_label})
    RETURN
        n AS source,
        m AS target,
        EXISTS((n)-[r]->(m)) AS source_is_subject,
        type(r) AS type,
        r.edge_label AS edge_label,
        r.relation AS relation,
        r.negated AS negated,
        r.id AS statement_id
    LIMIT {limit}
    """

    results = db.query(
        q,
        sources=s,
        targets=t,
        edge_label=edge_label,
        relation=relation,
        keywords=keywords,
        categories=categories,
        limit=size
    )

    statements = []

    for result in results:
        if result['source_is_subject']:
            s, o = result['source'], result['target']
        else:
            o, s = result['source'], result['target']

        s_categories = utils.standardize(s['category'])
        o_categories = utils.standardize(o['category'])

        if result['edge_label'] != None:
            edge_label = result['edge_label']
        else:
            edge_label = result['type']

        beacon_subject = BeaconStatementSubject(
            id=s['id'],
            name=s['name'],
            categories=s_categories
        )

        beacon_predicate = BeaconStatementPredicate(
            edge_label=edge_label,
            relation=result['relation'],
            negated=result['negated']
        )

        beacon_object = BeaconStatementObject(
            id=o['id'],
            name=o['name'],
            categories=o_categories
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
