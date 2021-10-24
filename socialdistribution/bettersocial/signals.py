from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Author


@receiver(signal = post_save, sender = User)
def create_user_author(sender, instance, created, **kwargs):
    """Saves an Author model when a NEW instance of a user has been created, enforcing the 1..1 relationship"""

    if created:
        Author.objects.create(user = instance)
