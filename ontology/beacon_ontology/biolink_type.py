class BiolinkType(object):
    def __init__(self, name, typeof, description=None, mappings=None, aliases=None):
        self.name = name
        self.typeof = typeof
        self.description = description
        self.mappings = [] if mappings is None else mappings
        self.aliases = [] if aliases is None else aliases
