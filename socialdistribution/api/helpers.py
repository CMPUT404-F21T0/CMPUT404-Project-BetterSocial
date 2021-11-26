import re
from typing import Optional, Union
from uuid import UUID

from bettersocial.models import UUIDRemoteCache, Node


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


def get_host_of_uuid(uuid: Union[str, UUID]) -> Optional[Node]:
    """Queries the cache for the node that hosts the object with this UUID"""
    if isinstance(uuid, str):
        uuid = UUID(uuid)

    queryset = UUIDRemoteCache.objects.filter(uuid = uuid)

    if not queryset.exists():
        return None

    return queryset.get().node


def cache_host_of_uuid(uuid: Union[str, UUID], node: Node):
    """Writes/overwrites to the UUID cache which node hosts the object specified by the UUID."""
    if isinstance(uuid, str):
        uuid = UUID(uuid)

    try:
        cached_object = UUIDRemoteCache.objects.filter(uuid = uuid).get()
        cached_object.node = node
        cached_object.save()
    except UUIDRemoteCache.DoesNotExist:
        UUIDRemoteCache.objects.create(uuid = uuid, node = node)
