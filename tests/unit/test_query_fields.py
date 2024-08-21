import pytest
from shotgun_extensions import sge_find, sge_find_one


@pytest.fixture(scope='function')
def sg(mocker):
    return mocker.patch('shotgun_extensions.query_fields.Shotgun', autospec=True)


def test_sge_find(sg, mocker):
    mocker.patch.object(sg, 'find', return_value=[
        {
            "type": "Shot",
            "id": 1
        },
        {
            "type": "Shot",
            "id": 2
        }
    ])
    mocker.patch('shotgun_extensions.query_fields.fetch_query_fields', return_value={
        "sg_test_query_field": {
            "type": "str"
        }
    })
    mocker.patch('shotgun_extensions.query_fields.add_query_fields_to_entity',
                 side_effect=[
                     {
                         "type": "Shot",
                         "id": 1,
                         "sg_test_query_field": "Test Value 1"
                     },
                     {
                         "type": "Shot",
                         "id": 2,
                         "sg_test_query_field": "Test Value 2"
                     }
                 ])

    filters = [["sg_scene", "is", {
        "type": "Scene",
        "id": 1
    }]]
    result = sge_find(sg, entity_type="Shot", logged_in_user=None, filters=filters, fields=['sg_test_query_field'])

    assert result == [
        {
            "type": "Shot",
            "id": 1,
            "sg_test_query_field": "Test Value 1"
        },
        {
            "type": "Shot",
            "id": 2,
            "sg_test_query_field": "Test Value 2"
        }
    ]
