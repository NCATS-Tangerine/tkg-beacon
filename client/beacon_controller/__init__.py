import os, yaml

basepath = os.path.dirname(os.path.abspath(__file__))

configpath = os.path.join(basepath, 'config', 'config.yaml')

try:
    config = yaml.safe_load(open(configpath).read())
except IOError as e:
    raise Exception('Failed to open configuration file at {}, try running "make configure" and setting up resulting config file'.format(configpath))

from . import utils, database

from .controllers.concepts_controller import get_concept_details, get_concepts, get_exact_matches_to_concept_list
from .controllers.metadata_controller import get_concept_categories, get_knowledge_map, get_predicates
from .controllers.statements_controller import get_statement_details, get_statements
