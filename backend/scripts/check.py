
from pyiceberg.catalog import load_catalog
cat = load_catalog("rest", uri="http://localhost:8181", warehouse="s3://test")
print(cat.list_namespaces())
