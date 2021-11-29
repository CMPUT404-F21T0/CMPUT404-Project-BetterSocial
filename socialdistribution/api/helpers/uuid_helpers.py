import re
from typing import Optional
from uuid import UUID

# Doesn't need to be esacped because it'll be substituted in later -- also a raw string
UUID_MATCH_STRING = r'[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{4}-?[0-9a-fA-F]{12}'


def remove_uuid_dashes(uuid_str: str):
    """Removes the dashes from uuid strings, because DRF can't do that apparently."""
    return re.sub('([0-9a-fA-F]{8})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{4})-([0-9a-fA-F]{12})', '\\1\\2\\3\\4\\5', uuid_str)


def extract_author_uuid_from_id(id: str) -> Optional[UUID]:
    """Extracts the author UUID from a 'http://<host>/author/<uuid>' type string"""

    # Returns group 1, the first capture group, as a UUID
    match = re.search(fr'http.*?authors?/({UUID_MATCH_STRING})/?', id)

    if match is None or match.group(1) is None:
        return None

    return UUID(match.group(1))


def extract_post_uuid_from_id(id: str) -> Optional[UUID]:
    """Extracts the post UUID from a 'http://<host>/author/<a_uuid>/post/<uuid>' type string"""

    # Returns group 1, the first capture group, as a UUID
    match = re.search(fr'http.*?authors?/.*?/posts/({UUID_MATCH_STRING})/?', id)

    if match is None or match.group(1) is None:
        return None

    # Note the 2, since we want the second capture group
    return UUID(match.group(1))
