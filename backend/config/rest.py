from pyiceberg.catalog import load_catalog


CATALOG_NAME = "default"
NAMESPACE_NAME = "user_events"

catalog = load_catalog(
    name=CATALOG_NAME,
    uri="http://iceberg-rest:8181",
    type="rest",
    s3__access_key_id="admin",
    s3__secret_access_key="password",
    # s3__path_style_access="true"
)
