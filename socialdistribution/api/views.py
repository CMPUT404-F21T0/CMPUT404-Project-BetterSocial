from collections import OrderedDict
from uuid import UUID

from django.contrib.auth.models import User
from django.db.models import Q
from rest_framework import viewsets, mixins, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from api import pagination
from api import serializers
from bettersocial import models
from bettersocial.models import Post, InboxItem, Node


# -- API SPEC -- #

class AuthorViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.UpdateModelMixin):
    queryset = models.Author.objects.all()
    serializer_class = serializers.AuthorSerializer
    pagination_class = pagination.CustomPageNumberPagination

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        root_json = OrderedDict()

        root_json['type'] = 'authors'
        root_json['items'] = response.data

        response.data = root_json

        return response


# class FollowerViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin):
#     queryset = models.Follower


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

        # Modify the request via the adapter method
        if isinstance(request.user, Node):
            request = request.user.adapter.post_inbox_item(request, *args, **kwargs)

        return super().create(request, *args, **kwargs)

    def list(self, request, *args, **kwargs):

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
        if not isinstance(request.user, User):
            raise PermissionDenied({ 'message': "You must be authenticated as a user to get post items this way!" })

        data = list()

        # Dirtiest hack but hey it works
        queryset = InboxItem.objects.filter(author = request.user.author, inbox_object__iregex = '"type": "post"').all()

        for item in queryset:
            data.append(item.inbox_object)

        return Response(data)


class AllPostsViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    """Helper view to get all of the posts that the user should see"""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.PostSerializer

    def list(self, request, *args, **kwargs):
        if not isinstance(request.user, User):
            raise PermissionDenied({ 'message': "You must be authenticated as a user to get post items this way!" })

        self.kwargs['author_uuid'] = request.user.author.uuid

        return super().list(request, *args, **kwargs)

    def get_queryset(self):

        author_uuid = self.kwargs['author_uuid']

        return Post.objects.filter(
            (Q(visibility = Post.Visibility.PUBLIC)) |
            (Q(visibility = Post.Visibility.FRIENDS) & Q(author__follower__follower_uuid = author_uuid) & Q(author__following__following_uuid = author_uuid)) |
            (Q(visibility = Post.Visibility.PRIVATE) & Q(recipient_uuid = author_uuid))
        ).distinct().order_by('-published')
