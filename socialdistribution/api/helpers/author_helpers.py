from typing import Set, List
from uuid import UUID

from rest_framework.request import Request

from api import serializers
from bettersocial.models import Author
from . import remote_helpers


def get_author_friends(request: Request, author: Author) -> List:
    """Get all the author's friends, including remote ones"""

    following = { f.following_uuid for f in author.following_set.all() }
    followers = { f.follower_uuid for f in author.follower_set.all() }

    # Set intersection of APPROVED followers and people you've followed
    uuid_set: Set[UUID] = followers & following

    # This will hold local and remote author objects, as JSON
    friends = list()

    for uuid_item in uuid_set:
        try:
            local_author: Author = Author.objects.filter(uuid = uuid_item).get()

            # IFF the author we're trying to verify friendship with has APPROVED our request (meaning there would be an entry in local_author FOLLOWERS), proceed.
            if local_author.follower_set.filter(follower_uuid = author.uuid):
                friends.append(serializers.AuthorSerializer(local_author, context = { 'request': request }).data)

        except Author.DoesNotExist:
            # If the author does not exist locally, find it remotely
            remote_author_json = remote_helpers.find_remote_author(uuid_item)

            # If found AND the remote author has approved our follow, add, if not, ignore
            if remote_author_json and remote_helpers.approved_follow(uuid_item, author.uuid):
                friends.append(remote_author_json)

    return friends


def get_author_friends_as_uuid(author: Author) -> List[UUID]:
    """Get all the author's friends, including remote ones, as UUIDs (i.e. does not need request)"""

    following = { f.following_uuid for f in author.following_set.all() }
    followers = { f.follower_uuid for f in author.follower_set.all() }

    # Set intersection of APPROVED followers and people you've followed
    uuid_set: Set[UUID] = followers & following

    # This will hold local and remote author objects, as uuids
    friends = list()

    for uuid_item in uuid_set:
        try:
            local_author: Author = Author.objects.filter(uuid = uuid_item).get()

            # IFF the author we're trying to verify friendship with has APPROVED our request (meaning there would be an entry in local_author FOLLOWERS), proceed.
            if local_author.follower_set.filter(follower_uuid = author.uuid):
                friends.append(uuid_item)

        except Author.DoesNotExist:
            # If the author does not exist locally, find it remotely
            remote_author_json = remote_helpers.find_remote_author(uuid_item)

            # If found AND the remote author has approved our follow, add, if not, ignore
            if remote_author_json and remote_helpers.approved_follow(uuid_item, author.uuid):
                friends.append(remote_author_json)

    return friends
