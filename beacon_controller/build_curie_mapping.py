"""
This preprocessing step is needed for scigraph, which uses IRIs rather than
CURIEs as identifiers. The process is to pull down all kinds of IRIs one by one
and commit them and their CURIE mapping to memory.
"""
import beacon_controller.database as neo4j

from beacon_controller import utils
from beacon_controller import namespace as ns
from beacon_controller import config

from prefixcommons import contract_uri as _contract_uri
from prefixcommons.curie_util import default_curie_maps

from collections import defaultdict

from typing import List, Set

from tinydb import TinyDB, Query

default_curie_maps += [{
    'OMIM' : 'http://omim.org/entry/',
    'NCBIGenome' : 'https://www.ncbi.nlm.nih.gov/genome/',
    'doi' : 'https://doi.org/',
    'ElementsOfMorphology' : 'https://elementsofmorphology.nih.gov/index.cgi?tid=',
    'HttpsElementsOfMorphology' : 'http://elementsofmorphology.nih.gov/index.cgi?tid=',
    'ElementsOfMorphologyImages' : 'https://elementsofmorphology.nih.gov/images/terms/',
    'MedecineSymbol' : 'http://genatlas.medecine.univ-paris5.fr/fiche.php?symbol=',
    'GuideToPharmacology' : 'http://www.guidetopharmacology.org/GRAC/ObjectDisplayForward?objectId=',
    'NCBIGene' : 'https://www.ncbi.nlm.nih.gov/gene/',
    'OMIA' : 'https://omia.org/',
    'SANGER' : 'https://decipher.sanger.ac.uk/syndrome/',
    'NCBITerm' : 'https://www.ncbi.nlm.nih.gov/assembly?term=',
    'NCBIBook' : 'https://www.ncbi.nlm.nih.gov/books/',
    'PhenotypicSeries' : 'http://www.omim.org/phenotypicSeries/',
    'MousePhenotypeParameters' : 'https://www.mousephenotype.org/impress/parameters/',
    'EBI' : 'http://www.ebi.ac.uk/efo/'
    'EBIVariant' : 'https://www.ebi.ac.uk/gwas/variants/',
}]

ignore = [
    'https://raw.githubusercontent.com/monarch-initiative/GENO-ontology/develop/src/ontology/imports/',
    'http://www.ncbi.nlm.nih.gov/bookshelf/br.fcgi',
    'https://raw.githubusercontent.com/monarch-initiative/GENO-ontology',
    "_:",
    'http://owlcollab.github.io/oboformat/doc/obo-syntax.html',
    'https://github.com/obophenotype/uberon/wiki/Taxon-constraints',
    'http://www.geneontology.org/page/go-slim-and-subset-guide',
    'http://robot.obolibrary.org/reason',
    'https://github.com/obophenotype/uberon/wiki/inter-anatomy-ontology-bridge-ontologies',
    'http://protege.stanford.edu/plugins/owl/protege#defaultLanguage',
    'http://robot.obolibrary.org/extract',
    'http://robot.obolibrary.org/template',
    'https://github.com/dosumis/dead_simple_owl_design_patterns/',
    'http://robot.obolibrary.org/filter',
    'https://github.com/INCATools/ontology-starter-kit/issues/50',
    'https://elementsofmorphology.nih.gov/',
    'mailto:bfo-owl-devel@googlegroups.com',
    'https://www.bcm.edu/',
    'https://mbp.mousebiology.org/',
    'https://www.har.mrc.ac.uk/',
    'https://www.helmholtz-muenchen.de/en/',
    'https://www.mouseclinic.de/',
    'https://www.jax.org/',
    'https://www.mousephenotype.org/',
    'https://github.com/information-artifact-ontology',
    'https://en.wikipedia.org/wiki/Extract,_transform,_load',
    'https://archive.monarchinitiative.org/201803/ttl/udp.ttl',

]

def common_prefix(s:str, t:str) -> str:
    """
    Finds the common prefix between s and t
    """
    for i, (a, b) in enumerate(zip(s, t)):
        if a != b:
            return s[0:i]
    return s

def contract_uri(uri:str) -> str:
    curies = _contract_uri(uri)

    if len(curies) == 0:
        return None

    curies.sort(key=len)

    return curies[0]

def reduce(uris:Set[str]):
    """
    Takes a set of URIs and returns the set of longest common prefixes
    """
    discovered_prefixes = set()
    for uri in uris:
        prefixes = [common_prefix(uri, s) for s in uris - set([uri])]
        prefixes.sort(key=len, reverse=True)
        if len(prefixes) != 0:
            discovered_prefixes.add(prefixes[0])
    return discovered_prefixes

def discover(uris:List[str]):
    while True:
        size = len(uris)
        uris = reduce(uris)
        if size != len(uris):
            return uris

def run():
    id = utils.get(config, 'concepts', 'properties', 'id', default='id')

    mapping = {}
    skipped = list()
    discovered_prefixes = set()

    while True:
        size = len(mapping)

        q = f"""
        MATCH (n) WHERE
            NONE(p IN {{prefixes}} WHERE n.{id} STARTS WITH p)
        RETURN DISTINCT
            n.{id} AS id
        LIMIT 2000;
        """
        # import pudb; pu.db

        nodes = neo4j.query(q, prefixes=list(mapping.keys()) + ignore + list(skipped))

        for node in nodes:
            uri = node['id']
            curie = contract_uri(uri)

            if curie is None:
                # quit('No mapping for ' + uri)
                skipped.append(uri)
                continue

            prefix, key = curie.split(':')

            if key is '':
                skipped.append(uri)
                continue

            uri_prefix, _ = uri.split(key)

            if uri_prefix not in mapping:
                print(prefix, ':', uri_prefix)
            mapping[uri_prefix] = prefix

        # if len(skipped) > 10:
        #     discovered_prefixes |= discover(skipped)
        #     print()
        #     print(discovered_prefixes)

        skipped = list(skipped)
        skipped.sort()
        if len(skipped) > 100:
            for s in skipped:
                print(s)
            quit()

        if len(nodes) == 0:
            return mapping

if __name__ == '__main__':
    mapping = run()
    print()
    print('done')
    print()
    for k, v in mapping.items():
        print(k, ':', v)
