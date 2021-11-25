import re
from typing import Optional

from uuid import UUID


def remove_uuid_dashes(uuid_str: str):
    """Removes the dashes from uuid strings, because DRF can't do that apparently."""
    return re.sub('([0-9a-fA-F]{8})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{12})', '\\1\\2\\3\\4\\5', uuid_str)


def extract_uuid_from_id(id: str) -> Optional[UUID]:
    """Extracts the author UUID from a 'http://<host>/author/<uuid>' type string"""

    # Returns group 1, the first capture group, as a UUID
    match = re.search('http.*?authors?/([0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12})/?', id)

    if match is None:
        return None

    return UUID(match.group(1))
