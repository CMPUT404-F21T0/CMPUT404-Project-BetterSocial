from collections import OrderedDict
from uuid import UUID

from django.contrib.auth.models import User
from rest_framework import viewsets, mixins, permissions
from rest_framework.exceptions import PermissionDenied

from api import serializers
from bettersocial import models
from bettersocial.models import Post, InboxItem, Node


class AuthorViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.UpdateModelMixin):
    queryset = models.Author.objects.all()
    serializer_class = serializers.AuthorSerializer

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

    def get_queryset(self):
        return InboxItem.objects.filter(author_id = self.kwargs['author_pk']).all()

    def create(self, request, *args, **kwargs):

        # Modify the request via the adapter method
        if isinstance(request.user, Node):
            request = request.user.adapter.postInboxItem(request, *args, **kwargs)

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


class PostLikeViewSet(viewsets.ModelViewSet):
    queryset = models.Like.objects.all()
    serializer_class = serializers.PostLikeSerializer
