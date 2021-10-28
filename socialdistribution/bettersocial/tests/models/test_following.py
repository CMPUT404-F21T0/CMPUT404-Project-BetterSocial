from django.test import TestCase

from bettersocial.models import Following
from bettersocial.tests import utils


class FollowingModelTests(TestCase):

    def setUp(self) -> None:
        super().setUp()

        self.author = utils.create_test_user(username = 'author').author
        self.author_following = utils.create_test_user(username = 'following').author

        # The author sets himself as following the second author. The row is registered under the author's FK
        self.following = utils.create_test_following(self.author, self.author_following.uuid)

    def test_delete_cascade(self):
        """Tests that the Following object is deleted when the associated author is deleted"""

        author_id = self.author.uuid

        self.assertTrue(Following.objects.filter(author_id = author_id, following_uuid = self.author_following.uuid).exists())

        self.author.delete()

        self.assertFalse(Following.objects.filter(author_id = author_id, following_uuid = self.author_following.uuid).exists())

    def test_parent_relation(self):
        """Tests that the relationship accessor refers to the same author and following UUID that we set up"""

        self.assertTrue(self.following.author, self.author)
        self.assertTrue(self.following.following_uuid, self.author_following.uuid)
