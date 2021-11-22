from collections import OrderedDict

from rest_framework import viewsets, mixins

from api import serializers
from bettersocial import models
from bettersocial.models import Post


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


class CommentLikeViewSet(viewsets.ModelViewSet):
    queryset = models.Like.objects.all()
    serializer_class = serializers.CommentLikeSerializer


class PostLikeViewSet(viewsets.ModelViewSet):
    queryset = models.Like.objects.all()
    serializer_class = serializers.PostLikeSerializer
