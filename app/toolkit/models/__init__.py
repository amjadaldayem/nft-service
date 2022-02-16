from jinja2 import Template

from app.models.dynamo import SchemaParser

meta_file_template = """
{% for schema in table_schemas %}
class {{ schema.name }}:
    \"\"\"
    {% if schema.mapped_classes %} Mapped classes:
    {% for klass in schema.mapped_classes %}
      - {{klass.key}} = {{klass.name}}
    {% endfor %}
    {% endif %}
    \"\"\"
    NAME = '{{ schema.table_name }}'  # Table Name
    {% for key_info in schema.key_info_list %}
    {{key_info.name}} = '{{key_info.value}}'  # {{key_info.comment}}
    {% endfor %}
{% endfor %}
"""


def do_generate_meta(schemas_file, output_file):
    """
    Generates meta-classes file from schema YAML to use with Dynamodb Repositories.
    """
    table_schemas = SchemaParser.load_schema_file(schemas_file)
    #
    template = Template(meta_file_template)

    table_schemas_transformed = []
    for table_schema in table_schemas.values():
        key_info_list = [
            {
                'name': 'PK',
                'value': table_schema.pk.attr_name,
                'comment': table_schema.pk.attr_value.strip('"')
            }
        ]
        if table_schema.sk:
            key_info_list.append(
                {
                    'name': 'SK',
                    'value': table_schema.sk.attr_name,
                    'comment': table_schema.sk.attr_value.strip('"')
                }
            )

        for gsi in table_schema.gsi_list:
            uname = gsi.name.upper().replace("GSI_", "")
            key_info_list.append(
                {
                    'name': 'GSI_' + uname,
                    'value': gsi.name,
                }
            )
            key_info_list.append(
                {
                    'name': 'GSI_' + uname + '_PK',
                    'value': gsi.pk.attr_name,
                    'comment': gsi.pk.attr_value.strip('"')
                }
            )
            if gsi.sk:
                key_info_list.append(
                    {
                        'name': 'GSI_' + uname + '_SK',
                        'value': gsi.sk.attr_name,
                        'comment': gsi.sk.attr_value.strip('"')
                    }
                )

        for lsi in table_schema.lsi_list:
            uname = lsi.name.upper().replace("LSI_", "")
            key_info_list.append(
                {
                    'name': 'LSI_' + uname,
                    'value': lsi.name,
                }
            )
            key_info_list.append(
                {
                    'name': 'LSI_' + uname + '_SK',
                    'value': lsi.sk.attr_name,
                    'comment': lsi.sk.attr_value.strip('"')
                }
            )
        c = {
            'table_name': table_schema.name,
            'name': 'DT' + table_schema.name.title() + 'Meta',
            'key_info_list': key_info_list,
        }
        if table_schema.model_classes:
            c['mapped_classes'] = [{
                'key': k, 'name': v.__name__
            } for k, v in table_schema.model_classes.items()]
        table_schemas_transformed.append(c)

    with open(output_file, 'w') as fd:
        fd.write(template.render(
            {
                'table_schemas': table_schemas_transformed
            }
        ))
