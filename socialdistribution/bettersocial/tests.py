from django.contrib.auth.models import User
from django.test import TestCase

from bettersocial.models import Author


class AuthorModelTests(TestCase):

    def setUp(self) -> None:
        super().setUp()

        self.user: User = User.objects.create(
            username = 'testuser',
            password = 'testuserpw',
            first_name = 'testuserfn',
            last_name = 'testuserln',
            email = 'testuser@email.example.com',
        )

        self.author: Author = Author.objects.get(user_id = self.user.id)

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
