from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Author


@receiver(signal = post_save, sender = User)
def create_user_author(sender, instance, created, **kwargs):
    """Saves an Author model when a NEW instance of a user has been created, enforcing the 1..1 relationship"""

    if created:
        Author.objects.create(user = instance)

# https://newbedev.com/create-user-inactive-as-default-is-active-default-false

@receiver(pre_save, sender=User)
def user_to_inactive(sender, instance, **kwargs):
    if instance._state.adding is True:
        print("Creating Inactive User")
        instance.is_active = False
        