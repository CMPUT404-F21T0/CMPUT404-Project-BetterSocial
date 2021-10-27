from django.test import TestCase

from bettersocial.models import Like, Author, Post, Comment
from bettersocial.tests import utils


class LikeModelTests(TestCase):

    def setUp(self) -> None:
        super().setUp()

        self.author: Author = utils.create_test_user().author
        self.post: Post = utils.create_test_post(author = self.author)
        self.comment: Comment = utils.create_test_comment(author_uuid = self.author.uuid, post = self.post)

        self.post_like: Like = utils.create_test_like(author_uuid = self.author.uuid, liked_object = self.post)
        self.comment_like: Like = utils.create_test_like(author_uuid = self.author.uuid, liked_object = self.comment)

    def test_delete_cascade(self):
        """Tests that the author object is deleted when the associated user is deleted"""

        # Save comment and post id to local var because it will be inaccessible after the delete
        comment_like_id = self.comment_like.id
        post_like_id = self.post_like.id

        # Make sure both exists before delete
        self.assertTrue(Like.objects.filter(id = comment_like_id).exists(), 'Like object associated with the Comment does not exist!')
        self.assertTrue(Like.objects.filter(id = post_like_id).exists(), 'Like object associated with the Post does not exist!')

        self.comment.delete()

        # Check that comment like DNE now, but post like still exists
        self.assertFalse(Like.objects.filter(id = comment_like_id).exists(), 'Like object was not deleted upon Comment deletion!')
        self.assertTrue(Like.objects.filter(id = post_like_id).exists(), 'Like object associated with the Post does not exist!')

        self.post.delete()

        # Now check that both DNE
        self.assertFalse(Like.objects.filter(id = comment_like_id).exists(), 'Like object was not deleted upon Comment deletion!')
        self.assertFalse(Like.objects.filter(id = post_like_id).exists(), 'Like object was not deleted upon Post deletion!')

    def test_parent_relation(self):
        """Tests that the relationship accessor refers to the same likeable object that we set up"""

        self.assertEquals(self.comment_like.object, self.comment)
        self.assertEquals(self.post_like.object, self.post)
