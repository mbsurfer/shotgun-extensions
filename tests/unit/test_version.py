import pytest
from src.shotgun_extensions import __version__

class TestVersion:
    def test_version(self):
        assert __version__ == '1.0.0'