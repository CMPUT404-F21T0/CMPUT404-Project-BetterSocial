import uuid

from django.test import TestCase

from bettersocial.models import Author, LikedRemote, Post
from bettersocial.tests import utils


class LikedRemoteModelTests(TestCase):

    def setUp(self) -> None:
        super().setUp()

        self.author: Author = utils.create_test_user().author

        self.object_uuid = uuid.uuid4()

        # The author is self-declaring that they liked something remotely. Remember this model is being used basically for caching purposes
        self.liked_remote = utils.create_test_liked_remote(author = self.author, object_uuid = self.object_uuid, model_type = Post)

    def test_delete_cascade(self):
        """Tests that the LikedRemote object is deleted when the associated author is deleted"""

        author_id = self.author.uuid

        self.assertTrue(LikedRemote.objects.filter(author_id = author_id, object_uuid = self.object_uuid).exists())

        self.author.delete()

        self.assertFalse(LikedRemote.objects.filter(author_id = author_id, object_uuid = self.object_uuid).exists())

    def test_parent_relation(self):
        """Tests that the relationship accessor refers to the same author that we set up"""

        self.assertTrue(self.liked_remote.author, self.author)
