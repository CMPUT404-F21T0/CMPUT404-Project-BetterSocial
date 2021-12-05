from collections import OrderedDict
from uuid import UUID

import requests
import yarl
from django.contrib.auth.models import User
from django.db.models import Q
from django.http.response import HttpResponseBadRequest, HttpResponseServerError
from requests.auth import HTTPBasicAuth
from rest_framework import viewsets, mixins, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from yarl import URL

from api import pagination
from api import serializers
from api.helpers import uuid_helpers
from bettersocial import models
from bettersocial.models import Post, InboxItem, Node, Author, Follower


# -- API SPEC -- #

class AuthorViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.UpdateModelMixin):
    queryset = models.Author.objects.all()
    serializer_class = serializers.AuthorSerializer
    pagination_class = pagination.CustomPageNumberPagination

    def list(self, request, *args, **kwargs):
        '''
        GET {host_url}/authors

        Gets all authors on the server
        '''
        response = super().list(request, *args, **kwargs)

        root_json = OrderedDict()

        root_json['type'] = 'authors'
        root_json['items'] = response.data

        response.data = root_json

        return response


class FollowerViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
    queryset = Follower.objects.none()
    serializer_class = serializers.AuthorSerializer

    def get_follower(self, follower_uuid, context):
        author = models.Author.objects.filter(uuid = self.kwargs['author_pk']).get()
        followers = models.Follower.objects.filter(author = author).all()

        follower_qs = followers.filter(follower_uuid = follower_uuid)
        if follower_qs.exists():
            # get author serialize
            author_qs = Author.objects.filter(uuid = follower_uuid)
            if author_qs.exists():
                author = author_qs.get()
                return serializers.AuthorSerializer(author, context = context).data
            else:
                # remote author, GET info
                remote_node_qs = models.UUIDRemoteCache.objects.filter(uuid = follower_uuid)
                if remote_node_qs.exists():
                    # TODO: GET it and set it to response.data

                    node = remote_node_qs.get()
                    url = (yarl.URL(node.host) / node.prefix / 'author' / follower_uuid / '').human_repr()

                    post_response = requests.get(
                        url,
                        headers = { 'Accept': 'application/json' },
                    )

                    post_response.raise_for_status()

                    if post_response.ok:
                        return serializers.AuthorSerializer(post_response.json(), context = context).data

        return None

    def retrieve(self, request, *args, **kwargs):
        """
        GET {host_url}/author/{author_uuid}/followers/{foreign_uuid}

        Checks if the provided foreign_uuid is a follower of the user
        """
        response = Response()
        # response = super().retrieve(request, *args, **kwargs)
        foreign_uuid = kwargs['pk']

        follower = self.get_follower(foreign_uuid, { 'request': request })

        if follower is not None:
            response.data = follower
        else:
            return HttpResponseServerError({ 'message': 'Follower exists locally but author cannot be found' })

        return response

    def list(self, request, *args, **kwargs):
        """
        GET {host_url}/author/{author_uuid}/followers

        Gets list of authors who are the author_uuid's followers
        """
        response = super().list(request, *args, **kwargs)
        response.data.append({'type': 'followers'})
        items = list()

        author = Author.objects.filter(uuid = kwargs['author_pk']).get()
        followers = Follower.objects.filter(author = author).all()
        for follower in followers:
            # follower_author = Author.objects.filter(uuid = follower.follower_uuid)
            follower_uuid = follower.follower_uuid
            follower_item = self.get_follower(follower_uuid, { 'request': request })

            if follower_item is not None:
                items.append(follower_item)
            else:
                return HttpResponseServerError({ 'message': f'Follower {follower_uuid} exists locally but author cannot be found' })

        response.data.append({'items': items})

        return response

    def update(self, request, *args, **kwargs):
        '''
        PUT {host_url}/author/{author_uuid}/followers/{foreign_uuid}

        Adds a follower (must be authenticated)
        '''
        if not isinstance(request.user, User):
            raise PermissionDenied({ 'message': "You must be authenticated as a user to get inbox items!" })

        if request.user.author.uuid != UUID(self.kwargs['author_pk']):
            raise PermissionDenied({ 'message': "You cannot get the inbox items of another user!" })

        response = super().update(request, *args, **kwargs)
        author = Author.objects.filter(uuid = kwargs['author_pk']).get()
        foreign_uuid = kwargs['pk']

        if not Follower.objects.filter(author = author, follower_uuid = foreign_uuid):
            Follower(author = author, follower_uuid = foreign_uuid)
            return response
        else:
            return HttpResponseServerError({ 'message': 'Author is already a follower' })

    def destroy(self, request, *args, **kwargs):
        '''
        DELETE {host_url}/author/{author_uuid}/followers/{foreign_uuid}

        Remove a follower
        '''
        foreign_uuid = kwargs['pk']
        author = Author.objects.filter(uuid = kwargs['author_pk']).get()
        followers_qs = Follower.objects.filter(author = author)
        follower_qs = followers_qs.filter(follower_uuid = foreign_uuid)
        if follower_qs.exists():
            Follower.objects.filter(follower_uuid = foreign_uuid).delete()
            return Response()
        else:
            return HttpResponseBadRequest({ 'message': 'Follower does not exist' })


class PostViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):
    serializer_class = serializers.PostSerializer
    pagination_class = pagination.CustomPageNumberPagination

    def get_queryset(self):
        return models.Post.objects.filter(author__uuid = self.kwargs['author_pk'], visibility = Post.Visibility.PUBLIC).all()


class CommentViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin):
    serializer_class = serializers.CommentSerializer

    def get_queryset(self):
        return models.Comment.objects.filter(post__uuid = self.kwargs['post_pk']).order_by('-published').all()

    def list(self, request, *args, **kwargs):
        '''
        GET {host_url}/author/{author_uuid}/posts/{post_uuid}/comments

        Gets comments of the given post
        '''
        response = super().list(request, *args, **kwargs)

        root_json = OrderedDict()

        root_json['type'] = 'comments'
        root_json['comments'] = response.data

        response.data = root_json

        return response


class InboxItemViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin):
    serializer_class = serializers.InboxItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = pagination.CustomPageNumberPagination

    def get_queryset(self):
        return InboxItem.objects.filter(author_id = self.kwargs['author_pk']).all()

    def get_serializer_context(self):
        context = super().get_serializer_context()

        # This is needed to know what author's inbox to save at
        context['author_id'] = self.kwargs['author_pk']

        return context

    def create(self, request, *args, **kwargs):
        '''
        POST {host_url}/author/{author_uuid}/inbox

        Sends a post to the author's inbox
        '''
        # Modify the request via the adapter method
        if isinstance(request.user, Node):
            request = request.user.adapter.post_inbox_item(request, *args, **kwargs)

        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):
        '''
        GET {host_url}/author/{author_uuid}/inbox

        Gets all inbox items sent to author (must be authenticated)
        '''
        if not isinstance(request.user, User):
            raise PermissionDenied({ 'message': "You must be authenticated as a user to get inbox items!" })

        if request.user.author.uuid != UUID(self.kwargs['author_pk']):
            raise PermissionDenied({ 'message': "You cannot get the inbox items of another user!" })

        return super().list(request, *args, **kwargs)


class CommentLikeViewSet(viewsets.ModelViewSet):
    queryset = models.Like.objects.all()
    serializer_class = serializers.CommentLikeSerializer
    pagination_class = pagination.CustomPageNumberPagination


class PostLikeViewSet(viewsets.ModelViewSet):
    queryset = models.Like.objects.all()
    serializer_class = serializers.PostLikeSerializer


# -- Helper Views - Local -- #

class AllRemotePostsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """Helper view to get all remote posts that are viewable to the current author"""

    queryset = Post.objects.none()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.PostSerializer

    def list(self, request, *args, **kwargs):
        '''
        GET {host_url}/remote-posts

        Gets all remote posts viewable to current author (must be authenticated)
        '''
        if not isinstance(request.user, User):
            raise PermissionDenied({ 'message': "You must be authenticated as a user to get post items this way!" })

        data = list()

        # Dirtiest hack but hey it works
        queryset = InboxItem.objects.filter(author = request.user.author, inbox_object__iregex = '"type": "post"').all()

        for item in queryset:

            if item.inbox_object['visibility'] == Post.Visibility.PUBLIC:

                node = Node.objects.filter(host__contains = item.inbox_object['author']['host']).get()

                response = requests.head(
                    URL(item.inbox_object['url']).human_repr(),
                    headers = { 'Accept': 'application/json' },
                    auth = HTTPBasicAuth(node.node_username, node.node_password),
                )

                print(f'Inbox checking: {response.status_code} -- {response.request.url}')

                # If the response to a public post comes back as 404 that means it was deleted, so the inbox item is invalid, so don't return it.
                if response.status_code == 404:
                    continue

            data.append(item.inbox_object)

        for post in data:
            # Make post UUID available in _uuid
            post['_uuid'] = uuid_helpers.extract_post_uuid_from_id(post['id']).hex

            # Make author UUID available in author._uuid
            post['author']['_uuid'] = uuid_helpers.extract_author_uuid_from_id(post['author']['id']).hex

        return Response(data)


class AllPostsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """Helper view to get all of the posts that the user should see"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.PostSerializer

    def list(self, request, *args, **kwargs):
        '''
        GET {host_url}/posts

        Gets all local posts viewable to current author (must be authenticated)
        '''
        if not isinstance(request.user, User):
            raise PermissionDenied({ 'message': "You must be authenticated as a user to get post items this way!" })

        self.kwargs['author_uuid'] = request.user.author.uuid

        response = super().list(request, *args, **kwargs)

        for post in response.data:
            # Make post UUID available in _uuid
            post['_uuid'] = uuid_helpers.extract_post_uuid_from_id(post['id']).hex

            # Make author UUID available in author._uuid
            post['author']['_uuid'] = uuid_helpers.extract_author_uuid_from_id(post['author']['id']).hex

        return response

    def get_queryset(self):

        author_uuid = self.kwargs['author_uuid']

        return Post.objects.filter(
            (Q(visibility = Post.Visibility.PUBLIC)) |
            (Q(visibility = Post.Visibility.FRIENDS) & Q(author__follower__follower_uuid = author_uuid) & Q(author__following__following_uuid = author_uuid)) |
            (Q(visibility = Post.Visibility.PRIVATE) & Q(recipient_uuid = author_uuid))
        ).distinct().order_by('-published')
