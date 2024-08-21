from dotenv import load_dotenv
import os
from pprint import pprint
import pytest

from shotgun_api3 import Shotgun
from shotgun_extensions import sge_find, sge_find_one

load_dotenv()

URL = os.getenv('URL', '')
SCRIPT_NAME = os.getenv('SCRIPT_NAME', '')
API_KEY = os.getenv('SCRIPT_KEY', '')

@pytest.fixture(scope='module')
def sg():
    return Shotgun(URL, SCRIPT_NAME, API_KEY)

def test_sge_find(sg):
    user = {
        "type": "HumanUser",
        "id": 50
    }
    filters = [["sg_scene", "is", {
        "type": "Scene",
        "id": 5024
    }]]
    result = sge_find(sg, entity_type="Shot", logged_in_user=user, filters=filters, fields=['sg_test_query_field'])
    pprint(result)

def test_sge_find_one(sg):
    user = {
        "type": "HumanUser",
        "id": 50
    }
    filters = [["sg_scene", "is", {
        "type": "Scene",
        "id": 5024
    }]]
    result = sge_find_one(sg, entity_type="Shot", logged_in_user=user, filters=filters, fields=['sg_test_query_field'])
    pprint(result)