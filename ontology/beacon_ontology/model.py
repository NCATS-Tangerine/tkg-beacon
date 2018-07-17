import yaml
import requests

from beacon_ontology.biolink_class import BiolinkClass
from beacon_ontology.biolink_slot import BiolinkSlot
from beacon_ontology.biolink_type import BiolinkType

_URI='https://raw.githubusercontent.com/biolink/biolink-model/master/biolink-model.yaml'

class BiolinkModel(object):
    """
    The constructor of this class downloads the biolink model and uses it to
    build up various classes and methods for discovering their mappings and
    inheritance.

    A biolink entity is a slot, type, or class in the biolink model
    """
    def __init__(self, uri=_URI):
        response = requests.get(uri)
        d = yaml.load(response.text)
        types = d['types']
        slots = d['slots']
        classes = d['classes']

        self.classes = []

        for c_name in classes:
            c = classes.get(c_name)
            b = BiolinkClass(
                name=c_name,
                description=c.get('description'),
                is_a=c.get('is_a'),
                abstract=c.get('abstract'),
                mappings=c.get('mappings'),
                aliases=c.get('aliases')
            )

            self.classes.append(b)

        self.types = []

        for t_name in types:
            t = types.get(t_name)
            if t is not None:
                b = BiolinkType(
                    name=t_name,
                    typeof=t.get('typeof'),
                    description=t.get('description'),
                    mappings=t.get('mappings'),
                    aliases=t.get('aliases')
                )

            self.types.append(b)

        self.slots = []

        for s_name in slots:
            s = slots.get(s_name)
            b = BiolinkSlot(
                name=s_name,
                description=s.get('description'),
                mappings=s.get('mappings'),
                is_a=s.get('is_a'),
                domain=s.get('domain'),
                range=s.get('range'),
                abstract=s.get('abstract'),
                aliases=s.get('aliases')
            )

            self.slots.append(b)

        self.__name_map = {}
        self.__mappings_map = {}
        self.__child_map = {}

        for s in self.slots + self.classes + self.types:
            self.__name_map[s.name] = s

            for m in s.mappings:
                self.__mappings_map[m] = s

            try:
                if s.is_a in self.__child_map:
                    self.__child_map[s.is_a].add(s)
                else:
                    self.__child_map[s.is_a] = set([s])
            except AttributeError:
                # Types do not have an is_a attribute
                pass



    def getEntityByName(self, name):
        """
        Returns a biolink entity with the given name
        """
        return self.__name_map.get(name)

    def getEntityByMapping(self, identifier):
        """
        Returns the biolink entity that identifier maps onto.
        """
        return self.__mappings_map.get(identifier)

    def getChildren(self, entity):
        """
        Returns the biolink entities that directly inherit from this entity
        """
        return self.__child_map.get(entity.name)

    def getParent(self, entity):
        if entity.is_a is None:
            return None
        else:
            return self.getEntityByName(entity.is_a)

    def getDescendants(self, entity):
        """
        Recursively builds and returns the biolink entities that inherit from
        this entity.
        """
        children = self.getChildren(entity)

        if children is None:
            return set()
        else:
            descendants = set(children)
            for child in children:
                descendants |= self.getDescendants(child)

            return descendants

    def getAncestors(self, entity):
        """
        Recursively builds and returns a set of biolink entities that this
        entity inherits from.
        """
        if entity.is_a is None:
            return set()
        else:
            parent = self.getEntityByName(entity.is_a)
            return {parent} | self.getAncestors(parent)
