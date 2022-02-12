import os.path

from app import settings
from app.models.dynamo import SchemaParser


def create_tables(client):
    schema_file = os.path.join(
        settings.PROJECT_BASE_PATH,
        'app',
        'models',
        'schemas.yml'
    )
    table_schema_dict = SchemaParser.load_schema_file(schema_file)
    for _, v in table_schema_dict.items():
        v.create_from_api(client)
