from shotgun_api3 import Shotgun
from dataclasses import dataclass
from typing import Optional, Union


def sge_find(shogun_api: Shotgun, logged_in_user: dict = None,  **kwargs) -> list[dict]:
    """
    Find entities using the ShotGrid API and add query fields to the entity dictionary.

    :param shogun_api:
    :param logged_in_user:
    :param kwargs:
    :return:
    """
    entities = shogun_api.find(**kwargs)
    if not entities:
        return []
    all_query_fields: Optional[dict] = fetch_query_fields(shogun_api, kwargs.get('entity_type'))
    fields = kwargs.get('fields', [])

    # filter out query fields where key is not in fields
    query_fields = {query_field: all_query_fields[query_field] for query_field in all_query_fields.keys() if query_field in fields}

    if query_fields:
        updated_entities = []
        for entity in entities:
            updated_entities.append(add_query_fields_to_entity(shogun_api, entity, query_fields, logged_in_user))
        return updated_entities

    return entities

def sge_find_one(shogun_api: Shotgun, logged_in_user: dict = None, **kwargs) -> Optional[dict]:
    entity = shogun_api.find_one(**kwargs)
    if not entity:
        return None
    all_query_fields: Optional[dict] = fetch_query_fields(shogun_api, kwargs.get('entity_type'))
    fields = kwargs.get('fields', [])

    # filter out query fields where key is not in fields
    query_fields = {query_field: all_query_fields[query_field] for query_field in all_query_fields.keys() if query_field in fields}

    if query_fields:
        return add_query_fields_to_entity(shogun_api, entity, query_fields, logged_in_user)
    return entity

def add_query_fields_to_entity(shogun_api: Shotgun, entity: dict, query_fields: dict, logged_in_user: dict = None) -> dict:
    """Add query fields to the entity dictionary."""
    for field_name, field_schema in query_fields.items():
        query_field = ShotGridQueryField(sg=shogun_api,
                                         field_name=field_name,
                                         field_schema=field_schema,
                                         parent_entity=create_related_entity_dict(entity),
                                         logged_in_user=logged_in_user)
        entity[field_name] = query_field.try_get_value()
    return entity

def fetch_query_fields(shogun_api: Shotgun, entity_type: str) -> dict:
    """Set query fields from the entity schema dictionary."""
    schema = shogun_api.schema_field_read(entity_type)
    return {field_name: field_definition for field_name, field_definition in schema.items() if
            'query' in field_definition['properties']}

def create_related_entity_dict(entity: Optional[dict]):
    """Create a dictionary with the entity type and ID."""
    if entity is None:
        return None
    return {'type': entity['type'], 'id': entity['id']}


@dataclass
class ShotGridQueryFieldFilter:
    active: str
    path: list
    relation: str
    values: list[str or dict]
    conditions: Optional[list['ShotGridQueryFieldFilter']]
    logical_operator: str
    qb_multivalued_condition_subgroup: bool
    tokens: dict

    @classmethod
    def from_dict(cls, d: dict, tokens=None):
        return cls(
            active=d.get('active', 'true'),  # default active to true, some query fields do not return this key
            path=d.get('path'),
            relation=d.get('relation'),
            values=d.get('values', []),
            conditions=[cls.from_dict(c, tokens=tokens) for c in d.get('conditions')] if d.get(
                'conditions') else None,
            logical_operator=d.get('logical_operator'),
            qb_multivalued_condition_subgroup=d.get('qb_multivalued_condition_subgroup'),
            tokens=tokens
        )

    @classmethod
    def format_entity_value(cls, entity_value: dict):
        return {
            'type': entity_value['type'],
            'id': entity_value['id']
        }

    def to_array(self):
        def convert_logical_operator(operator):
            if operator == "and":
                return "all"
            elif operator == "or":
                return "any"
            else:
                raise ValueError(f"Logical operator '{operator}' is not supported. Expecting values 'and' or 'or'.")

        if not self.is_active():
            return None
        if self.conditions:
            return {
                'filter_operator': convert_logical_operator(self.logical_operator),
                'filters': [f for f in (c.to_array() for c in self.conditions) if f is not None]
            }
        else:
            if isinstance(self.values[0], dict):
                """
                Expected Tokens:
                There is a case where shotgun references contextual entities such as the "Current Shot" or "Me"
                and sets the entity id to 0.
                {
                     'id': 0,
                     'name': 'Current Shot',
                     'type': 'Shot',
                     'valid': 'parent_entity_token'
                 }
                """
                if self.values[0].get('valid') == 'parent_entity_token':
                    return [self.path, self.relation, self.tokens.get('parent_entity_token')]
                elif self.values[0].get('valid') == 'logged_in_user_token':
                    return [self.path, self.relation, self.tokens.get('logged_in_user_token')]
                elif self.values[0].get('id') == 0:
                    return None
                else:
                    return [self.path, self.relation, self.format_entity_value(self.values[0])]
            return [self.path, self.relation, self.values]

    def is_active(self):
        return self.active == "true"


class ShotGridQueryField:

    def __init__(self, sg: Shotgun, field_name: str, field_schema: dict, parent_entity: dict = None,
                 logged_in_user: dict = None):
        self._sg = sg
        self._field_name = field_name
        self._field_schema = field_schema
        self._parent_entity = parent_entity
        self._logged_in_user = logged_in_user
        self._field_properties = field_schema.get('properties', None)
        if not self._field_properties:
            raise ValueError(f"ShotGridQueryField {field_name} is missing required key: properties")

        query_value = self._field_properties.get('query', None).get('value', None)
        if not query_value:
            raise ValueError(f"ShotGridQueryField {field_name} is missing required key: properties.query.value")

        self._filters = query_value.get('filters', None)
        if not self._filters:
            raise ValueError(f"ShotGridQueryField {field_name} is missing required key: properties.query.value.filters")

        self._entity_type = query_value.get('entity_type', None)
        if not self._entity_type:
            raise ValueError(
                f"ShotGridQueryField {field_name} is missing required key: properties.query.value.entity_type")

    def try_get_value(self) -> str:
        try:
            value_type = self.get_summary_default()
            # all entities, a single entity, or a number of entities
            # the name "single_record" is misleading
            if value_type == 'single_record':
                return self._query_records()
            # summary of a field calculated by percentage
            elif value_type == 'percentage':
                return self._query_percentage()
            # Entity count
            elif value_type == 'record_count':
                return self._query_record_count()
            # summary of a field calculated by count, sum, average, minimum, or maximum
            elif value_type in ['count', 'sum', 'average', 'minimum', 'maximum']:
                return self._query_aggregate(aggregate_type=value_type)
            else:
                raise ValueError(
                    f"ShotGridQueryField({self._field_name}) encountered an unsupported value_type: {value_type}.")
        except Exception as e:
            return ''

    def _query_records(self) -> str:
        def value_or_name(value: Union[str, dict]):
            return value.get('name') if isinstance(value, dict) else value

        filters = self._get_filter_array()
        field = self.get_summary_field()
        order = self._get_order_array()
        limit = self._get_limit()

        results = self._sg.find(entity_type=self._entity_type, filters=filters, fields=[field],
                                order=order, limit=limit)
        if not results:
            return ''
        joined_results = ', '.join([value_or_name(entity.get(field)) or '' for entity in results])
        return joined_results

    def _query_percentage(self) -> str:
        filters = self._get_filter_array()
        field = self.get_summary_field()
        summary_value = self.get_summary_value()
        summary_fields = [{'field': field, 'type': 'percentage', 'value': summary_value}]
        summary = self._sg.summarize(entity_type=self._entity_type, filters=filters, summary_fields=summary_fields)
        return f"{summary['summaries'][field]}% {summary_value}"

    def _query_aggregate(self, aggregate_type: str) -> str:
        filters = self._get_filter_array()
        field = self.get_summary_field()
        summary_fields = [{'field': field, 'type': aggregate_type}]
        summary = self._sg.summarize(entity_type=self._entity_type, filters=filters, summary_fields=summary_fields)
        return f"{summary['summaries'][field]}"

    def _query_record_count(self) -> str:
        filters = self._get_filter_array()
        summary_fields = [{'field': 'id', 'type': 'count'}]
        summary = self._sg.summarize(entity_type=self._entity_type, filters=filters, summary_fields=summary_fields)
        return str(summary['summaries']['id'])

    def get_summary_field(self):
        summary_field_dict = self._field_properties.get('summary_field', None)
        if not summary_field_dict:
            raise ValueError(f"ShotGridQueryField {self._field_name} is missing expected key: properties.summary_field")
        summary_field_value = summary_field_dict.get('value', None)
        if not summary_field_value:
            raise ValueError(
                f"ShotGridQueryField {self._field_name} is missing expected key: properties.summary_field.value")
        return summary_field_value

    def get_summary_value(self):
        summary_value_dict = self._field_properties.get('summary_value', None)
        if not summary_value_dict:
            raise ValueError(
                f"ShotGridQueryField {self._field_name} is missing expected key: properties.summary_value")
        summary_value_value = summary_value_dict.get('value', None)
        if not summary_value_value:
            raise ValueError(
                f"ShotGridQueryField {self._field_name} is missing expected key: properties.summary_value.value")
        return summary_value_value

    def get_summary_default(self):
        summary_default_dict = self._field_properties.get('summary_default', None)
        if not summary_default_dict:
            raise ValueError(
                f"ShotGridQueryField {self._field_name} is missing expected key: properties.summary_default")
        summary_default_value = summary_default_dict.get('value', None)
        if not summary_default_value:
            raise ValueError(
                f"ShotGridQueryField {self._field_name} is missing expected key: properties.summary_field.value")
        return summary_default_value

    def _get_filter_array(self):
        """
        Converts the filter schema into an array of filters that can be used in the ShotGrid API.
        """
        filter_array = []
        query_condition_groups = self._filters.get('conditions', None)
        for conditions in query_condition_groups:
            query_field_condition = ShotGridQueryFieldFilter.from_dict(conditions, tokens=self._create_tokens())
            formatted_condition = query_field_condition.to_array()
            if formatted_condition:
                filter_array.append(formatted_condition)
        return filter_array

    def _create_tokens(self):
        return {
            'parent_entity_token': self._parent_entity,
            'logged_in_user_token': self._logged_in_user
        }

    def _get_order_array(self) -> Optional[list]:
        """
        Converts the order schema into an array of orders that can be used in the ShotGrid API.
        """
        summary_value = self.get_summary_value()
        if summary_value:
            return [
                {'field_name': summary_value['column'], 'direction': summary_value['direction']}
            ]
        return None

    def _get_limit(self) -> int:
        """
        Extract the limit from the summary_value schema else set to 1.
        """
        summary_value = self.get_summary_value()
        if summary_value:
            return summary_value.get('limit', 1)
        return 1