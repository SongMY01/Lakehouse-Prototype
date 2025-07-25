from pyiceberg.catalog import load_catalog

NAMESPACE_NAME = "user_events"

catalog = load_catalog(
    name="rest",
    uri="http://rest:8181",
    warehouse="s3://rest-bucket",
    properties={"s3.endpoint": "http://localhost:9000"},
)