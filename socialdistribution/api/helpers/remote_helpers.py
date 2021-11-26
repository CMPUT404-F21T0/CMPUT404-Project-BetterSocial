from sys import stderr
from typing import Optional, Union, Dict
from uuid import UUID

from bettersocial.models import UUIDRemoteCache, Node
from . import uuid_helpers


def get_node_of_uuid(uuid: Union[str, UUID]) -> Optional[Node]:
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


def find_remote_author(author_uuid: Union[str, UUID]) -> Optional[Dict]:
    if isinstance(author_uuid, str):
        author_uuid = UUID(author_uuid)

    cached_node = get_node_of_uuid(author_uuid)

    if cached_node:
        response = cached_node.adapter.get_author(cached_node, author_uuid)

        print(f'\nresponse from node {cached_node.host}:')
        print(response)
        print(response.request.url)

        # Found user, cache and return
        if response.status_code == 200:
            return response.json()

        print(f'Could not find UUID "{author_uuid}" on {cached_node.host}\'s server! Perhaps the user was deleted?', file = stderr)

    else:
        for node in Node.objects.all():
            response = node.adapter.get_author(node, author_uuid)

            print(f'\nresponse from node {node.host}:')
            print(response)
            print(response.request.url)

            # Found user, cache and return
            if response.status_code == 200:
                cache_host_of_uuid(author_uuid, node)
                return response.json()

        print(f'Could not find UUID "{author_uuid}" on any remote server! Perhaps the user was deleted?', file = stderr)
        return None


def approved_follow(remote_uuid: Union[str, UUID], author_uuid: Union[str, UUID]) -> bool:
    if isinstance(remote_uuid, str):
        remote_uuid = UUID(remote_uuid)

    if isinstance(author_uuid, str):
        author_uuid = UUID(author_uuid)

    cached_node = get_node_of_uuid(remote_uuid)

    if cached_node:
        # Get remote user's follower's list
        response = cached_node.adapter.get_followers(cached_node, remote_uuid)

        print(f'\nresponse from node {cached_node.host}:')
        print(response)
        print(response.json())
        print(response.request.url)

        # Check all of their followers -- IFF we find one whose UUID matches our own author's UUID, then we know they have approved the follow.
        if response.status_code == 200:
            for author_json in response.json()['items']:
                if author_uuid == uuid_helpers.extract_uuid_from_id(author_json['id']):
                    return True

    else:
        for node in Node.objects.all():
            # Get remote user's follower's list
            response = node.adapter.get_followers(node, remote_uuid)

            print(f'\nresponse from node {node.host}:')
            print(response)
            print(response.json() if response.status_code == 200 else None)
            print(response.request.url)

            # Check all of their followers -- IFF we find one whose UUID matches our own author's UUID, then we know they have approved the follow.
            if response.status_code == 200:

                cache_host_of_uuid(remote_uuid, node)

                for author_json in response.json()['items']:
                    if author_uuid == uuid_helpers.extract_uuid_from_id(author_json['id']):
                        return True

    return False
