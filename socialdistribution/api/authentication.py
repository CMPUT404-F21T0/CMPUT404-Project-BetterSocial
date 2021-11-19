from django.utils.translation import gettext_lazy as _
from rest_framework import authentication
from rest_framework import exceptions

from bettersocial.models import Node


class NodeAuthentication(authentication.BasicAuthentication):
    """A subclass of BasicAuth that allows HTTP Basic Authorization credentials to be checked against the list of `Node`s, instead of `User`s."""

    def authenticate_credentials(self, userid, password, request = None):

        node = Node.objects.filter(auth_username = userid, auth_password = password).first()

        if node is None:
            raise exceptions.AuthenticationFailed(_('Invalid username/password.'))

        # I know we should really be returning a more complete User-like object here, but since this is used only really for DRF, it doesn't really matter. This middleware will not be active for the regular app.
        # A benefit of this approach (albeit a less than ideal one) is that any view can test the type of `request.user` to see if a node or regular user has logged in, enabling different behaviour for each type.
        return node, None
