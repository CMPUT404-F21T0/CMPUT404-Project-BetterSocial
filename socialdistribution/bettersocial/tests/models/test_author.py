from django.contrib.auth.models import User
from django.test import TestCase

from bettersocial.models import Author, Following, Follower
from bettersocial.tests import utils


class AuthorModelTests(TestCase):

    def setUp(self) -> None:
        super().setUp()

        self.user: User = utils.create_test_user()

        try:
            self.author: Author = Author.objects.get(user_id = self.user.id)
        except Author.DoesNotExist as e:
            raise Author.DoesNotExist('An author object was NOT created when the user was created. Please make sure the signal is loaded properly and try again.') from e

    def test_display_name(self):
        """Tests that the display name returned by the dynamic property is correct"""

        self.assertEqual(self.author.display_name, f'{self.user.first_name} {self.user.last_name}')

    def test_delete_cascade(self):
        """Tests that the author object is deleted when the associated user is deleted"""

        # Save user_id to local var because it will be inaccessible after the delete
        user_id = self.user.id

        # Make sure it exists before delete
        self.assertTrue(Author.objects.filter(user_id = user_id).exists(), 'Author object associated with the user does not exist!')

        self.user.delete()

        # Make sure it DNE after delete
        self.assertFalse(Author.objects.filter(user_id = user_id).exists(), 'Author object was not deleted upon user deletion!')

    def test_parent_relation(self):
        """Tests that the relationship accessor refers to the same user that we set up"""

        self.assertEquals(self.author.user, self.user)

    def test_friends_with(self):
        """Tests that the friends_with method works properly, using local author objects."""

        author2: Author = utils.create_test_user(username = 'test_user_2').author

        self.assertFalse(self.author.friends_with(author2.uuid))
        self.assertFalse(author2.friends_with(self.author.uuid))

        # Adding a follower on behalf of `author` involves two operations: `author` recording that they follow `author2`, and "telling" `author2` that `author` follows them.
        following = Following.objects.create(author = self.author, following_uuid = author2.uuid)
        follower = Follower.objects.create(author = author2, follower_uuid = self.author.uuid)

        self.assertFalse(self.author.friends_with(author2.uuid))
        self.assertFalse(author2.friends_with(self.author.uuid))

        # Adding a follower on behalf of `author2` involves two operations: `author2` recording that they follow `author`, and "telling" `author` that `author2` follows them.
        Following.objects.create(author = author2, following_uuid = self.author.uuid)
        Follower.objects.create(author = self.author, follower_uuid = author2.uuid)

        # Once all 4 relations exist, we test that either author follows the other
        self.assertTrue(self.author.friends_with(author2.uuid))
        self.assertTrue(author2.friends_with(self.author.uuid))

        following.delete()
        follower.delete()

        # Here we test the other way around, making sure that removing the first Following/Follower set (aka `author` unfollowing `author2`) will invalidate their friendship
        self.assertFalse(self.author.friends_with(author2.uuid))
        self.assertFalse(author2.friends_with(self.author.uuid))
