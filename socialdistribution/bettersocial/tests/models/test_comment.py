from django.test import TestCase

from bettersocial.models import Author, Post, Comment
from bettersocial.tests import utils


class CommentModelTests(TestCase):

    def setUp(self) -> None:
        super().setUp()

        self.author: Author = utils.create_test_user().author
        self.post: Post = utils.create_test_post(author = self.author)

        self.comment: Comment = utils.create_test_comment(author_uuid = self.author.uuid, post = self.post)

    def test_delete_cascade(self):
        """Tests that the comment object is deleted when the associated post is deleted"""

        # Save post id to local var because it will be inaccessible after the delete
        post_uuid = self.post.uuid

        # Make sure both exists before delete
        self.assertTrue(Comment.objects.filter(post_id = post_uuid).exists(), 'Comment object associated with the Post does not exist!')

        self.post.delete()

        # Now check that both DNE
        self.assertFalse(Comment.objects.filter(post_id = post_uuid).exists(), 'Comment object was not deleted upon Post deletion!')

    def test_parent_relation(self):
        """Tests that the relationship accessor refers to the same post that we set up"""

        self.assertEquals(self.comment.post, self.post)
