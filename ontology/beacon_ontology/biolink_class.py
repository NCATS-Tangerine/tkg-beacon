class BiolinkClass(object):
    def __init__(self, name, description=None, is_a=None, abstract=None, mappings=None, aliases=None):
        self.name = name
        self.description = description
        self.is_a = is_a
        self.is_abstract = abstract
        self.mappings = [] if mappings is None else mappings
        self.aliases = [] if aliases is None else aliases
