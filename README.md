# shotgun_extensions

shotgun_extensions extends the functionality of shotgun_api3 Python package.

Quick example:

```python
>> > from shotgun_api3 import Shotgun
>> > from shotgun_extensions import sge_find_one
>> > sg = Shotgun('https://your-server.com', script_name='Script Name', api_key='scrip_api_key')
>> > my_shot = sge_find_one(sg, entity_type='Shot',
                            filters=[['code', 'is', '101_001_0001']],
                            fields=['name', 'query_field'])
>> > print(my_shot)

[{'name': '101_001_0001', 'query_field': 'value'}]
```

## Supported Features

### Query Fields

Currently, the ShotGun API does not support requesting query field values in the response from methods such as find and
find_one.

In order to get these values, you must request the entity schema and parse the response to generate additional queries
to the API.

See https://community.shotgridsoftware.com/t/api-to-get-query-field-values/11263 for details.

The query_fields module provides two methods that are meant to replace the find and find_one methods from the
shotgun_api3 package:

- sge_find
- sge_find_one

There is an optional parameter you can use with these functions called "logged_in_user." This is for you to pass a user
entity that will be used whenever you are referencing "Me" in one of your query fields in ShotGun.

The expected format is as follows:

```python
{
    'type': 'HumanUser',
    'id': 1234
}
```

## Install

You need Python 3.7 or newer.

You can install the library like this (preferably in a [virtualenv](https://virtualenv.pypa.io/en/stable/)):

```
pip install shotgun-extensions
```