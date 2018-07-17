import unittest

import beacon_ontology as onto

class TestBiolinkModel(unittest.TestCase):

    def test_mapping_uniqueness(self):
        model = onto.BiolinkModel()

        for entity in model.classes + model.slots:
            for identifier in entity.mappings:
                other = onto.getEntityByMapping(identifier)
                self.assertTrue(other is not None)
                self.assertEqual(entity.name, other.name, identifier + ' maps onto ' + other.name + ', expected: ' + entity.name)

    def test_name_lookup(self):
        # Slot
        self.assertEqual(onto.getEntityByName('causes').name, 'causes')
        # Type
        self.assertEqual(onto.getEntityByName('quotient').name, 'quotient')
        # Class
        self.assertEqual(onto.getEntityByName('disease').name, 'disease')

    def test_mapping_lookup(self):
        self.assertEqual(onto.getEntityByMapping('UMLSSG:DISO').name, 'disease')
        self.assertEqual(onto.getEntityByMapping('UO:0000105').name, 'frequency value')
        self.assertEqual(onto.getEntityByMapping('SEMMEDDB:STIMULATES').name, 'positively regulates, entity to entity')

    def test_get_data_works(self):
        self.assertTrue(onto.getSlots() is not None)
        self.assertTrue(onto.getTypes() is not None)
        self.assertTrue(onto.getClasses() is not None)

    def test_inheritance_lookup(self):
        c = onto.getEntityByMapping('SIO:010004')

        self.assertEqual(c.name, 'chemical substance')

        parent = onto.getParent(c)
        self.assertEqual(parent.name, 'molecular entity')

        children = onto.getChildren(parent)
        self.assertTrue(c in children)

        ancestors = onto.getAncestors(c)
        self.assertTrue(parent in ancestors)

        ancestor = onto.getEntityByName('biological entity')
        self.assertTrue(ancestor in ancestors)

        descendants = onto.getDescendants(parent)
        self.assertTrue(c in descendants)

        descendant = onto.getEntityByName('drug')
        self.assertTrue(descendant in descendants)

if __name__ == '__main__':
    unittest.main()
