class BiolinkSlot(object):
    def __init__(self, name, description=None, mappings=None, is_a=None, domain=None, range=None, abstract=None, aliases=None):
        self.name = name
        self.description = description
        self.mappings = [] if mappings is None else mappings
        self.is_a = is_a
        self.domain = domain
        self.range = range
        self.is_abstract = abstract
        self.aliases = [] if aliases is None else aliases
