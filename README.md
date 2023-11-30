# Crunch those QuerySets

qscruncher aims to solve two common issues causing performance bottlenecks:

* Missing select_related / prefetch_related
* Complex nested serializer overhead, especially with Django Rest Framework ModelSerializer

## Missing select_related / prefetch related

A common performance issue is, that an API listing with complex relations ends up doing
thousands of redundant SQL queries while fetching data one by one. qscruncher will do 
you a favour and break your tests if you try to access a foreign relation that 
is not cached. In production, it's a bit more forgiving and will issue only a warning. 

## Serializer overhead

qscruncher tries to be quick while doing minimal amount of introspection.


## Configuration

* `QSCRUNCHER_UNCACHED_RELATION_SIGNAL)` - An optional 
 django signal handler that is triggered if an uncached relation is encountered with a `msg` keyword.
* `QSCRUNCHER_UNCACHED_RELATION_NO_WARN` - Set to `True` to disable warning logging
* `QSCRUNCHER_UNCACHED_RELATION_NO_RAISE` - Set to `True` to disable raising exceptions