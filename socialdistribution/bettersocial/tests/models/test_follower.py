from django.test import TestCase

from bettersocial.models import Follower
from bettersocial.tests import utils


class FollowerModelTests(TestCase):

    def setUp(self) -> None:
        super().setUp()

        self.author = utils.create_test_user(username = 'author').author
        self.author_follower = utils.create_test_user(username = 'follower').author

        # The follower notifies author that they are following them. The row is registered under the author's FK
        self.follower = utils.create_test_follower(self.author, self.author_follower.uuid)

    def test_delete_cascade(self):
        """Tests that the Follower object is deleted when the associated author is deleted"""

        author_id = self.author.uuid

        self.assertTrue(Follower.objects.filter(author_id = author_id, follower_uuid = self.author_follower.uuid).exists())

        self.author.delete()

        self.assertFalse(Follower.objects.filter(author_id = author_id, follower_uuid = self.author_follower.uuid).exists())

    def test_parent_relation(self):
        """Tests that the relationship accessor refers to the same author and follower UUID that we set up"""

        self.assertTrue(self.follower.author, self.author)
        self.assertTrue(self.follower.follower_uuid, self.author_follower.uuid)
