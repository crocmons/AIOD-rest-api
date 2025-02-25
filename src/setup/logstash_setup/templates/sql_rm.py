TEMPLATE_SQL_RM = """SELECT
    {{entity_name}}.identifier,
    {{entity_name}}.date_deleted
FROM aiod.{{entity_name}}
INNER JOIN aiod.aiod_entry ON aiod.{{entity_name}}.aiod_entry_identifier=aiod.aiod_entry.identifier
WHERE (
aiod.{{entity_name}}.date_deleted IS NOT NULL
AND aiod.{{entity_name}}.date_deleted > :sql_last_value
) OR aiod.aiod_entry.status!='PUBLISHED'
"""
