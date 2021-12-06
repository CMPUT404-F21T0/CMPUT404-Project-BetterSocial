import uuid as uuid
from uuid import UUID

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType as DjangoContentType
from django.db import models
from markdownx.models import MarkdownxField

from api import adapters
from api.adapters import BaseAdapter
from .validators import validate_categories


# https://stackoverflow.com/questions/54802616/how-to-use-enums-as-a-choice-field-in-django-model
class ContentType(models.TextChoices):
    PLAIN = 'text/plain', 'Text'
    MARKDOWN = 'text/markdown', 'Markdown'
    BASE64 = 'application/base64', 'Base64 Encoded'
    IMAGE_PNG = 'image/png;base64', 'Image (PNG)'
    IMAGE_JPEG = 'image/jpeg;base64', 'Image (JPEG)'


class LocalAuthorMixin:
    @property
    def author_local(self) -> 'Author':
        """Tries to resolve the author_uuid to a local author on this server. Throws a DoesNotExist if the author cannot be found in the local database. This should be caught and handled appropriately by polling the other servers for the author"""

        # Massive code smell, I know -- but this is going to be refactored later into a helper function, rather than a mixin. I just need it to work for now.
        if isinstance(self, Like) or isinstance(self, Comment):
            uuid_param = self.author_uuid
        elif isinstance(self, Follower):
            uuid_param = self.follower_uuid
        elif isinstance(self, Following):
            uuid_param = self.following_uuid
        else:
            raise NotImplementedError(f'This mixin is not supported on {type(self)} instances!')

        try:
            return Author.objects.get(uuid = uuid_param)
        except Author.DoesNotExist as e:
            raise Author.DoesNotExist(f'The author with uuid `{uuid_param}` could not be found locally! Perhaps this author exists on a remote server and you forgot to check for it?') from e


# -- Main Models -- #

class Author(models.Model):
    """AKA the profile of a user"""

    # Note: Registered as part of User

    type = "author"

    uuid = models.UUIDField(primary_key = True, default = uuid.uuid4)

    github_url = models.CharField(max_length = 255, null = True)

    # TODO: 2021-10-19 Deal with images
    # profile_image = models.ImageField(upload_to = '/images', null = True)

    # Associates a user with the author
    user = models.OneToOneField(User, on_delete = models.CASCADE)

    class Meta:
        verbose_name = 'Author'
        verbose_name_plural = 'Authors'

    @property
    def display_name(self) -> str:
        return f'{self.user.first_name} {self.user.last_name}'

    def friends_with(self, author_uuid: UUID) -> bool:
        return self.following_set.filter(following_uuid = author_uuid).exists() and self.follower_set.filter(follower_uuid = author_uuid).exists()

    def __str__(self):
        return str(self.user.first_name) + ' ' + str(self.user.last_name)


class Like(models.Model, LocalAuthorMixin):
    """Represents a like on a post or comment on this server. Because comments are necessarily attached to posts, we store comments from foreign sources here."""

    type = "like"

    likeable_models = models.Q(model = 'post') | models.Q(model = 'comment')

    # Should ideally be a FK BUT since foreign likes would be stored in this database (i.e. would be POSTed from another server), it could be violated -- because we don't store foreign users here. So it is more of a soft-FK via uuid
    author_uuid = models.UUIDField()

    # Used for determining which object this like belongs to
    dj_object_uuid = models.UUIDField()
    dj_content_type = models.ForeignKey(
        DjangoContentType,

        # Limits the polymorphic relation choices to ONLY the post and comment (only likeable objects)
        # https://stackoverflow.com/questions/6335986/how-can-i-restrict-djangos-genericforeignkey-to-a-list-of-models
        limit_choices_to = likeable_models,
        on_delete = models.CASCADE
    )

    object = GenericForeignKey('dj_content_type', 'dj_object_uuid')

    # A user should not be able to like the same object twice
    class Meta:
        verbose_name = 'Like'
        verbose_name_plural = 'Likes'

        unique_together = ['author_uuid', 'dj_object_uuid', 'dj_content_type']


class LikedRemote(models.Model):
    """Represents a like that a LOCAL user made to a remote location. Mostly used as a cache of sorts, because otherwise, we would have no record of the user's like after we send the POST to the remote server."""

    # This is always a like from local to remote, so it is necessarily dependent on local author. Local to local or remote to local should be queryable via Like
    author = models.ForeignKey(Author, on_delete = models.CASCADE)

    # UUID of the object (post/comment) on the remote server. Is a weak FK relationship because we don't store remote data for the most part
    object_uuid = models.UUIDField()

    # Used for determining which object this like belongs to. We don't need a GenericForeignKey relationship, because it would not actually resolve to an object, but we still want to know the type that the like belongs to.
    dj_content_type = models.ForeignKey(
        DjangoContentType,
        limit_choices_to = Like.likeable_models,
        on_delete = models.CASCADE
    )

    # A user should not be able to like the same object twice
    class Meta:
        verbose_name = 'Remote Like'
        verbose_name_plural = 'Remote Likes'

        unique_together = ['author', 'object_uuid']


class Likeable(models.Model):
    """Abstract object that can be liked. The point of this is to define the reverse relationship below."""

    # Defines the reverse of the relationship so any likeable model can go .objects.likes.all() or something similar
    like_set = GenericRelation(Like, object_id_field = 'dj_object_uuid', content_type_field = 'dj_content_type')

    class Meta:
        abstract = True


class Post(Likeable):
    """Represents a post made by a user. Can have multiple types and has visibility settings"""

    type = "post"

    class Visibility(models.TextChoices):
        PUBLIC = 'PUBLIC', 'Public'
        FRIENDS = 'FRIENDS', 'Friends'
        PRIVATE = 'PRIVATE', 'Private to Author (DM)'

    # UUID of the Post object
    uuid = models.UUIDField(primary_key = True, default = uuid.uuid4)

    author = models.ForeignKey(Author, on_delete = models.CASCADE)

    # Used to determine which author UUID the author of this post wants to send this post to. Does not mean anything unless the visibility is PRIVATE.
    recipient_uuid = models.UUIDField(null = True, blank = True)

    # Source URL of reshared posts. When WE write to the database, this should be set to the host of the post that we reshared.
    source = models.CharField(max_length = 255, null = True)

    # Origin URL of reshared posts. When WE write to the database, this should be set to whatever the origin
    origin = models.CharField(max_length = 255, null = True)

    # Soft enum type, enforced in Django, not database level
    content_type = models.CharField(max_length = 32, choices = ContentType.choices, default = ContentType.PLAIN)

    title = models.CharField(max_length = 255)
    content = MarkdownxField(null = True, blank = True)
    description = models.TextField(null = True, blank = True)

    # Validated as a JSON list of non-empty strings.
    categories = models.JSONField(validators = [validate_categories], default = list, blank = True)

    # Soft enum type, enforced in Django, not database level
    visibility = models.CharField(max_length = 32, choices = Visibility.choices, default = Visibility.PUBLIC)

    # Does not mean anything UNLESS the visibility is private. Image only posts should ALWAYS have this set to true
    unlisted = models.BooleanField(default = False, blank = True)

    # Automatically sets the time to now on add and does not allow updates to it -- https://docs.djangoproject.com/en/3.2/ref/models/fields/#django.db.models.DateField.auto_now_add
    published = models.DateTimeField(auto_now_add = True)

    class Meta:
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'

    def get_content_type(self) -> ContentType:
        """Gets the ContentType object of the current type (includes both value and label). This exists because the content_type field would only return the value, and you might want the label."""

        return ContentType[self.content_type]

    def get_visibility(self) -> Visibility:
        """Gets the Visibility object of the current type (includes both value and label). This exists because the visibility field would only return the value, and you might want the label."""

        return Post.Visibility[self.visibility]

    def __str__(self):
        # Had some issues
        return self.title  # + ' | ' + str(self.author.github_url)


class Comment(Likeable, LocalAuthorMixin):
    """Represents a comment on a post on this server. Because comments are necessarily attached to posts, we store comments from foreign sources here."""

    type = "comment"

    # UUID of the Comment object
    uuid = models.UUIDField(primary_key = True, default = uuid.uuid4)

    # Comment belongs to a post
    post = models.ForeignKey(Post, related_name = "comments", on_delete = models.CASCADE)

    # Should ideally be a FK BUT since foreign comments would be stored in this database (i.e. would be POSTed from another server), it could be violated -- because we don't store foreign users here. So it is more of a soft-FK via uuid
    author_uuid = models.UUIDField()

    # Reuse the same choices as post. Although TODO: 2021-10-21 image types may be rejected, that is TBD
    content_type = models.CharField(max_length = 32, choices = ContentType.choices, default = ContentType.PLAIN)
    comment = models.TextField()

    published = models.DateTimeField(auto_now_add = True)

    class Meta:
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'

    def get_content_type(self) -> ContentType:
        """Gets the ContentType object of the current type (includes both value and label). This exists because the content_type field would only return the value, and you might want the label."""

        return ContentType[self.content_type]

    def get_local_author_username(self):
        return Author.objects.filter(uuid = self.author_uuid).get().display_name

    def __str__(self):
        # TODO: 2021-10-28 query local authors display name through author uuid, for remote authors TBD
        return str(self.post.title) + ' | ' + str(Author.objects.filter(uuid = self.author_uuid).get().display_name)


class Follower(models.Model, LocalAuthorMixin):
    """Represents a single follow from SOME user (local or remote) to OUR user (local). A bidirectional relationship on Follower/Following implies friendship. IFF there is an entry in this table and NOT Following, this counts as a friend "request". An author would "approve" a friend request by following the author back, which would make an entry in the Following table."""

    author = models.ForeignKey(Author, on_delete = models.CASCADE)

    # Should ideally be a FK BUT since foreign follows would be stored in this database, it could be violated -- because we don't store foreign users here. So it is more of a soft-FK via uuid
    follower_uuid = models.UUIDField()

    # A user may not be followed by the same person twice
    class Meta:
        verbose_name = 'Follower'
        verbose_name_plural = 'Followers'

        unique_together = ['author', 'follower_uuid']


class Following(models.Model, LocalAuthorMixin):
    """Represents a single follow from OUR user (local) to SOME user (local or remote). A bidirectional relationship on Following/Follower implies friendship"""
    author = models.ForeignKey(Author, on_delete = models.CASCADE)

    # Should ideally be a FK BUT since foreign follows would be stored in this database, it could be violated -- because we don't store foreign users here. So it is more of a soft-FK via uuid
    following_uuid = models.UUIDField()

    # A user may not follow by the same person twice
    class Meta:
        verbose_name = 'Following'
        verbose_name_plural = 'Following'

        unique_together = ['author', 'following_uuid']


class InboxItem(models.Model):
    """Each row represents an object that is SENT to the user's inbox. This is a light model, as it only references rows"""

    author = models.ForeignKey(Author, on_delete = models.CASCADE)

    # Used for determining which object this row stores. We don't need a GenericForeignKey relationship, because it would not actually resolve to an object, but we still want to know the type.
    dj_content_type = models.ForeignKey(
        DjangoContentType,
        limit_choices_to = models.Q(model = 'post') | models.Q(model = 'comment') | models.Q(model = 'like') | models.Q(model = 'follower'),
        on_delete = models.CASCADE
    )

    # TODO: 2021-10-21 add proper validator
    # A minimal or full representation of the object. This object always exists elsewhere, this is effectively a reference to it, as the various fields in here would allow it to point to the right object.
    inbox_object = models.JSONField(default = dict)

    class Meta:
        verbose_name = 'InboxItem'
        verbose_name_plural = 'InboxItem'


# -- Utility -- #


class Node(AbstractBaseUser):
    """A bidirectional connection between this server and another. Subclasses AbstractBaseUser since we kind of use it as a user object."""

    # Unsets fields from AbstractBaseUser
    password = None
    last_login = None

    host = models.CharField(max_length = 255, unique = True)

    display_name = models.CharField(max_length = 127, blank = True)

    # prefix between the host and the api endpoints. Example http://myhost.com/service/my/api/call, where "service" is the prefix.
    prefix = models.CharField(max_length = 32, default = 'service', blank = True)

    # The adapter that this node uses
    adapter_id = models.CharField(max_length = 32, default = 'default', choices = [(x, x) for x in adapters.registered_adapters.keys()])

    # Auth given to connect to THIS server
    auth_username = models.CharField(max_length = 255)
    auth_password = models.CharField(max_length = 255)

    # Auth used to connect to THEIR server
    node_username = models.CharField(max_length = 255)
    node_password = models.CharField(max_length = 255)

    class Meta:
        verbose_name = 'Node'
        verbose_name_plural = 'Nodes'

    @property
    def adapter(self) -> BaseAdapter:
        adapter = adapters.registered_adapters.get(self.adapter_id)
        return adapter if adapter else adapters.registered_adapters.get('default')

    def get_username(self):
        return self.host

    def clean(self):
        pass

    def set_password(self, raw_password):
        raise NotImplementedError('This method is not implemented for the Node model!')

    def check_password(self, raw_password):
        raise NotImplementedError('This method is not implemented for the Node model!')

    def set_unusable_password(self):
        raise NotImplementedError('This method is not implemented for the Node model!')

    def has_usable_password(self):
        raise NotImplementedError('This method is not implemented for the Node model!')

    def _legacy_get_session_auth_hash(self):
        raise NotImplementedError('This method is not implemented for the Node model!')

    def get_session_auth_hash(self):
        raise NotImplementedError('This method is not implemented for the Node model!')

    @classmethod
    def get_email_field_name(cls):
        raise NotImplementedError('This method is not implemented for the Node model!')

    @classmethod
    def normalize_username(cls, username):
        raise NotImplementedError('This method is not implemented for the Node model!')


class UUIDRemoteCache(models.Model):
    """A database-level lookup table for caching where a certain uuid for something is stored. Over time, this will make it so we don't have to ping every node to know what server hosts whatever object we want. This should be second priority to checking local objects. So, if you want an author by uuid, check local storage, then check this table."""

    # Unique and indexed by default so accesses will be fast
    uuid = models.UUIDField(primary_key = True)

    # Holds the host and prefix for finding the resource, the api should bt the exact same otherwise
    node = models.ForeignKey(Node, on_delete = models.CASCADE)

    # Make this behave like a dict
    class Meta:
        verbose_name = 'UUID Remote Cache'
        verbose_name_plural = 'UUID Remote Cache'

        unique_together = ['uuid', 'node']
