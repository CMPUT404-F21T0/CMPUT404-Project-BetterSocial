from django.test import TestCase

from bettersocial.models import Post
from bettersocial.tests import utils


class PostModelTests(TestCase):

    def setUp(self) -> None:
        super().setUp()

        self.author = utils.create_test_user().author

        self.post = utils.create_test_post(author = self.author)

    def test_delete_cascade(self):
        """Tests that the Post object is deleted when the associated author is deleted"""

        author_id = self.author.uuid

        self.assertTrue(Post.objects.filter(author_id = author_id).exists())

        self.author.delete()

        self.assertFalse(Post.objects.filter(author_id = author_id).exists())

    def test_parent_relation(self):
        """Tests that the relationship accessor refers to the same author that we set up"""

        self.assertEqual(self.post.author, self.author)
