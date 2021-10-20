import uuid as uuid

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from .validators import validate_categories


class Author(models.Model):
    """AKA the profile of a user"""

    # Note: Registered as part of User

    # Importantly, not the primary key of the table. This is so we can be consistent
    uuid = models.UUIDField(unique = True, default = uuid.uuid4, editable = False)

    # Null means that it's the current host
    host = models.CharField(max_length = 255, null = True)

    github_url = models.CharField(max_length = 255, null = True)

    # TODO: 2021-10-19 Deal with images
    # profile_image = models.ImageField(upload_to = '/images', null = True)

    # Associates a user with the author
    user = models.OneToOneField(User, on_delete = models.CASCADE)


@receiver(signal = post_save, sender = User)
def create_user_author(sender, instance, created, **kwargs):
    """Saves an Author model when a NEW instance of a user has been created, enforcing the 1..1 relationship"""
    if created:
        Author.objects.create(user = instance)


class Post(models.Model):
    """Represents a post made by a user. Can have multiple types and has visibility settings"""

    # https://stackoverflow.com/questions/54802616/how-to-use-enums-as-a-choice-field-in-django-model
    class ContentType(models.TextChoices):
        PLAIN = 'text/plain', 'Text'
        MARKDOWN = 'text/markdown', 'Markdown'
        BASE64 = 'application/base64', 'Base64 Encoded'
        IMAGE_PNG = 'image/png', 'Image (PNG)'
        IMAGE_JPEG = 'image/jpeg', 'Image (JPEG)'

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

        return self.ContentType[self.content_type]

    def get_visibility(self) -> Visibility:
        """Gets the Visibility object of the current type (includes both value and label). This exists because the visibility field would only return the value, and you might want the label."""

        return Post.Visibility[self.visibility]
