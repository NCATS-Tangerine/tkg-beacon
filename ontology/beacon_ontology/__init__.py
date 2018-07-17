"""
This module wraps a BiolinkModel instance and allows you to call its methods for
convenience.
"""


from beacon_ontology.model import BiolinkModel

_model = BiolinkModel()

def getSlots():
    return _model.slots

def getClasses():
    return _model.classes

def getTypes():
    return _model.types

def getEntityByName(name):
    return _model.getEntityByName(name)

def getEntityByMapping(identifier):
    return _model.getEntityByMapping(identifier)

def getChildren(entity):
    return _model.getChildren(entity)

def getParent(entity):
    return _model.getParent(entity)

def getDescendants(entity):
    return _model.getDescendants(entity)

def getAncestors(entity):
    return _model.getAncestors(entity)

def reloadModel(uri):
    global _model
    _model = BiolinkModel(uri)
