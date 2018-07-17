# Installation

Use Python 3, and install through `setup.py`:

```shell
$ python setup.py install
```

# Usage:

```python
>>> import beacon_ontology as onto
>>> c = onto.getEntityByMapping('UMLSSG:DISO')
>>> print(c)
<beacon_ontology.biolink_class.BiolinkClass object at 0x7f62f1f067b8>
>>> print(c.name)
disease
>>> print(c.mappings)
['MONDO:0000001', 'WD:Q12136', 'SIO:010299', 'UMLSSG:DISO']

```

Look at `test.py` for tests and other examples
of usage.
