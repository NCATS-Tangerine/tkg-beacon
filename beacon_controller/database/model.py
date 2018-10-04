from neomodel import StructuredNode, StructuredRel, StringProperty, ArrayProperty, RelationshipTo, RelationshipFrom

class Edge(StructuredRel):
    edge_label = StringProperty(required=True)
    relation = StringProperty()
    is_defined_by = StringProperty(required=True)
    provided_by = StringProperty(required=True)
    publications = ArrayProperty(StringProperty())
    evidence_type = StringProperty()
    qualifiers = ArrayProperty(StringProperty())
    negated = StringProperty()

class Node(StructuredNode):
    curie = StringProperty(required=True, db_property='id')
    uri = StringProperty(db_property='uri')
    name = StringProperty(required=True)
    category = ArrayProperty(required=True)
    description = StringProperty(db_property='description')
    symbol = StringProperty()
    edges = RelationshipTo('Node', 'EDGE', model=Edge)
