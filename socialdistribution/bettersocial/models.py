import uuid as uuid

from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType as DjangoContentType
from django.db import models

from .validators import validate_categories


# https://stackoverflow.com/questions/54802616/how-to-use-enums-as-a-choice-field-in-django-model
class ContentType(models.TextChoices):
    PLAIN = 'text/plain', 'Text'
    MARKDOWN = 'text/markdown', 'Markdown'
    BASE64 = 'application/base64', 'Base64 Encoded'
    IMAGE_PNG = 'image/png', 'Image (PNG)'
    IMAGE_JPEG = 'image/jpeg', 'Image (JPEG)'


# -- Main Models -- #


class Author(models.Model):
    """AKA the profile of a user"""

    type = "Author"

    # Note: Registered as part of User

    # Importantly, not the primary key of the table. This is so we can be consistent
    uuid = models.UUIDField(unique = True, default = uuid.uuid4, editable = False)

    github_url = models.CharField(max_length = 255, null = True)

    # TODO: 2021-10-19 Deal with images
    # profile_image = models.ImageField(upload_to = '/images', null = True)

    # Associates a user with the author
    user = models.OneToOneField(User, on_delete = models.CASCADE)


class Like(models.Model):
    """Represents a like on a post or comment on this server. Because comments are necessarily attached to posts, we store comments from foreign sources here."""

    type = "Like"

    likeable_models = models.Q(model = 'post') | models.Q(model = 'comment')

    # Should ideally be a FK BUT since foreign likes would be stored in this database (i.e. would be POSTed from another server), it could be violated -- because we don't store foreign users here. So it is more of a soft-FK via uuid
    author = models.UUIDField()

    # Used for determining which object this like belongs to
    dj_object_id = models.PositiveIntegerField()
    dj_content_type = models.ForeignKey(
        DjangoContentType,

        # Limits the polymorphic relation choices to ONLY the post and comment (only likeable objects)
        # https://stackoverflow.com/questions/6335986/how-can-i-restrict-djangos-genericforeignkey-to-a-list-of-models
        limit_choices_to = likeable_models,
        on_delete = models.CASCADE
    )

    object = GenericForeignKey('dj_content_type', 'dj_object_id')

    # A user should not be able to like the same object twice
    class Meta:
        unique_together = ['author', 'dj_object_id', 'dj_content_type']


class LikedRemote(models.Model):
    """Represents a like that a LOCAL user made to a remote location. Mostly used as a cache of sorts, because otherwise, we would have no record of the user's like after we send the POST to the remote server."""

    # This is always a like from local to remote, so it is necessarily dependent on local author. Local to local or remote to local should be queryable via Like
    author = models.ForeignKey(Author, on_delete = models.CASCADE)

    # UUID of the object (post/comment) on the remote server. Is a weak FK relationship because we don't store remote data for the most part
    uuid_object = models.UUIDField()

    # Used for determining which object this like belongs to. We don't need a GenericForeignKey relationship, because it would not actually resolve to an object, but we still want to know the type that the like belongs to.
    dj_content_type = models.ForeignKey(
        DjangoContentType,
        limit_choices_to = Like.likeable_models,
        on_delete = models.CASCADE
    )

    # A user should not be able to like the same object twice
    class Meta:
        unique_together = ['author', 'uuid_object']


class Likeable(models.Model):
    """Abstract object that can be liked. The point of this is to define the reverse relationship below."""

    # Defines the reverse of the relationship so any likeable model can go .objects.likes.all() or something similar
    likes = GenericRelation(Like, object_id_field = 'dj_object_id', content_type_field = 'dj_content_type')

    class Meta:
        abstract = True


class Post(Likeable):
    """Represents a post made by a user. Can have multiple types and has visibility settings"""

    type = "Post"

    class Visibility(models.TextChoices):
        PUBLIC = 'PUBLIC', 'Public'
        FRIENDS = 'FRIENDS', 'Friends'

    # UUID of the POST. Like Author, it's not the PK but it is unique.
    uuid = models.UUIDField(unique = True, default = uuid.uuid4, editable = False)

    author = models.ForeignKey(Author, on_delete = models.CASCADE)

    # Soft enum type, enforced in Django, not database level
    content_type = models.CharField(max_length = 32, choices = ContentType.choices, default = ContentType.PLAIN)

    title = models.CharField(max_length = 255)
    description = models.TextField()
    content = models.TextField()

    # Validated as a JSON list of non-empty strings.
    categories = models.JSONField(validators = [validate_categories], default = list)

    # Soft enum type, enforced in Django, not database level
    visibility = models.CharField(max_length = 32, choices = Visibility.choices, default = Visibility.PUBLIC)

    unlisted = models.BooleanField(default = False)

    # Automatically sets the time to now on add and does not allow updates to it -- https://docs.djangoproject.com/en/3.2/ref/models/fields/#django.db.models.DateField.auto_now_add
    published = models.DateTimeField(auto_now_add = True)

    def get_content_type(self) -> ContentType:
        """Gets the ContentType object of the current type (includes both value and label). This exists because the content_type field would only return the value, and you might want the label."""

        return ContentType[self.content_type]

    def get_visibility(self) -> Visibility:
        """Gets the Visibility object of the current type (includes both value and label). This exists because the visibility field would only return the value, and you might want the label."""

        return Post.Visibility[self.visibility]


class Comment(Likeable):
    """Represents a comment on a post on this server. Because comments are necessarily attached to posts, we store comments from foreign sources here."""

    type = "Comment"

    # UUID of the COMMENT. Like Author, it's not the PK but it is unique.
    uuid = models.UUIDField(unique = True, default = uuid.uuid4, editable = False)

    # Comment belongs to a post
    post = models.ForeignKey(Post, on_delete = models.CASCADE)

    # Should ideally be a FK BUT since foreign comments would be stored in this database (i.e. would be POSTed from another server), it could be violated -- because we don't store foreign users here. So it is more of a soft-FK via uuid
    author = models.UUIDField()

    # Reuse the same choices as post. Although TODO: 2021-10-21 image types may be rejected, that is TBD
    content_type = models.CharField(max_length = 32, choices = ContentType.choices, default = ContentType.PLAIN)
    comment = models.TextField()

    published = models.DateTimeField(auto_now_add = True)


class Follower(models.Model):
    """Represents a single follow from SOME user (local or remote) to OUR user (local). A bidirectional relationship on Follower/Following implies friendship. IFF there is an entry in this table and NOT Following, this counts as a friend "request". An author would "approve" a friend request by following the author back, which would make an entry in the Following table."""

    author = models.ForeignKey(Author, on_delete = models.CASCADE)

    # Should ideally be a FK BUT since foreign follows would be stored in this database, it could be violated -- because we don't store foreign users here. So it is more of a soft-FK via uuid
    follower = models.UUIDField()

    # A user may not be followed by the same person twice
    class Meta:
        unique_together = ['author', 'follower']


class Following(models.Model):
    """Represents a single follow from OUR user (local) to SOME user (local or remote). A bidirectional relationship on Following/Follower implies friendship"""

    author = models.ForeignKey(Author, on_delete = models.CASCADE)

    # Should ideally be a FK BUT since foreign follows would be stored in this database, it could be violated -- because we don't store foreign users here. So it is more of a soft-FK via uuid
    following = models.UUIDField()

    # A user may not follow by the same person twice
    class Meta:
        unique_together = ['author', 'following']


class Inbox(models.Model):
    """Each row represents an object that is SENT to the user's inbox."""

    author = models.ForeignKey(Author, on_delete = models.CASCADE)

    # TODO: 2021-10-21 add proper validator
    # A minimal or full representation of the object. This object always exists elsewhere, this is effectively a reference to it, as the various fields in here would allow it to point to the right object.
    object = models.JSONField(default = dict)


# -- Utility -- #


class Node(models.Model):
    """A bidirectional connection between this server and another."""

    host = models.CharField(max_length = 255, unique = True)

    # prefix between the host and the api endpoints. Example http://myhost.com/service/my/api/call, where "service" is the prefix.
    prefix = models.CharField(max_length = 32, default = 'service')

    # Auth given to connect to THIS server
    auth_username = models.CharField(max_length = 255)
    auth_password = models.CharField(max_length = 255)

    # Auth used to connect to THEIR server
    node_username = models.CharField(max_length = 255)
    node_password = models.CharField(max_length = 255)


class UUIDRemoteCache(models.Model):
    """A database-level lookup table for caching where a certain uuid for something is stored. Over time, this will make it so we don't have to ping every node to know what server hosts whatever object we want. This should be second priority to checking local objects. So, if you want an author by uuid, check local storage, then check this table."""

    # TODO: 2021-10-21 WIP

    # Unique and indexed by default so accesses will be fast
    # TODO: 2021-10-20 add validator
    uuid = models.UUIDField(primary_key = True)

    dj_content_type = models.ForeignKey(
        DjangoContentType,

        # These are the choices that are the most readily cacheable
        limit_choices_to = models.Q(model = 'author') | models.Q(model = 'post') | models.Q(model = 'comment'),
        on_delete = models.CASCADE
    )

    # Holds the host and prefix for finding the resource, the api should bt the exact same otherwise
    node = models.ForeignKey(Node, on_delete = models.CASCADE)

    # Make this behave like a dict
    class Meta:
        unique_together = ['uuid', 'dj_content_type']
