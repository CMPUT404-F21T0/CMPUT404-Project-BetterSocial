from typing import Union, Dict
from uuid import UUID

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType as DjangoContentType

from bettersocial.models import Author, Post, Comment, Like, LikedRemote, Follower, Following, Inbox


def create_test_user(
        username: str = 'test_user',
        password: str = 'test_user_pw',
        first_name: str = 'test_user_fn',
        last_name: str = 'test_user_ln',
        email: str = 'testuser@email.example.com'
):
    """
    Creates a test user with reasonable defaults. Should ideally create
    """
    return User.objects.create(
        username = username,
        password = password,
        first_name = first_name,
        last_name = last_name,
        email = email,
    )


def create_test_like(
        author_uuid: UUID,
        liked_object: Union[Post, Comment],
):
    """
    Creates a test Like with some reasonable defaults
    """

    return Like.objects.create(
        author_uuid = author_uuid,
        object = liked_object,
    )


def create_test_liked_remote(
        author: Author,
        object_uuid: UUID,
):
    """
    Creates a test LikeRemote object with some reasonable defaults
    """

    return LikedRemote(
        author = author,
        object_uuid = object_uuid,
    )


def create_test_post(
        author: Author,
        title: str = 'Test Post Title',
        description: str = 'Test Post Description',
        content: str = 'Test Post Content',
        **kwargs
):
    """
    Creates a test Post with some reasonable defaults

    **kwargs are for arguments that have model defaults, or are nullable in the model. These include:
    - recipient_uuid: UUID
    - source: str
    - origin: str
    - content_type: str
    - categories: List[str]
    - visibility: str
    - unlisted: bool
    - published: datetime
    """

    return Post.objects.create(
        author = author,
        title = title,
        description = description,
        content = content,
        **kwargs
    )


def create_test_comment(
        author_uuid: UUID,
        post: Post,
        comment: str = 'Test Comment',
        **kwargs
):
    """
    Creates a test Comment with some reasonable defaults

    **kwargs are for arguments that have model defaults, or are nullable in the model. These include:
    - content_type: models.ContentType
    - published: datetime
    """

    return Comment.objects.create(
        post = post,
        author_uuid = author_uuid,
        comment = comment,
        **kwargs
    )


def create_test_follower(
        author: Author,
        follower_uuid: UUID,
):
    """
    Creates a test Follower with some reasonable defaults
    """

    return Follower.objects.create(
        author = author,
        follower_uuid = follower_uuid
    )


def create_test_following(
        author: Author,
        following_uuid: UUID,
        **kwargs
):
    """
    Creates a test Following with some reasonable defaults

    **kwargs are for arguments that have model defaults, or are nullable in the model. These include:
    - dj_content_type: django.contrib.contenttypes.models.ContentType
    """

    return Following.objects.create(
        author = author,
        following_uuid = following_uuid,
        **kwargs
    )


def create_test_inbox_entry(
        author: Author,
        dj_content_type: DjangoContentType,
        inbox_object: Dict
):
    """
    Creates a test Inbox entry with some reasonable defaults
    """

    return Inbox.objects.create(
        author = author,
        dj_content_type = dj_content_type,
        object = inbox_object
    )
