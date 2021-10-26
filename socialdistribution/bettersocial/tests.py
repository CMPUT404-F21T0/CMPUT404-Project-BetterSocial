from django.contrib.auth.models import User
from django.test import TestCase

from bettersocial.models import Author


class AuthorModelTests(TestCase):

    def setUp(self) -> None:
        super().setUp()

        self.testUser: User = User.objects.create(
            username = 'testuser',
            password = 'testuserpw',
            first_name = 'testuserfn',
            last_name = 'testuserln',
            email = 'testuser@email.example.com',
        )

        self.testAuthor: Author = self.testUser.author

    def test_display_name(self):
        """Tests that the display name returned by the dynamic property is correct"""

        self.assertEqual(self.testAuthor.display_name, f'{self.testUser.first_name} {self.testUser.last_name}')
