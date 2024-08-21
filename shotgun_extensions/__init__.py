from pkg_resources import get_distribution
from shotgun_extensions.query_fields import sge_find, sge_find_one

__version__ = get_distribution('shotgun_extensions').version
