from collections import OrderedDict

from rest_framework import viewsets, mixins

from api import serializers
from bettersocial import models


class PostViewSet(viewsets.ModelViewSet):
    queryset = models.Post.objects.all()
    serializer_class = serializers.PostSerializer

    def retrieve(self, request, *args, **kwargs):
        print(self.get_serializer())

        return super().retrieve(request, *args, **kwargs)


class AuthorViewSet(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.ListModelMixin, mixins.UpdateModelMixin):
    queryset = models.Author.objects.all()
    serializer_class = serializers.AuthorSerializer

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)

        new_response = OrderedDict()

        new_response['type'] = 'followers'
        new_response['items'] = response.data

        response.data = new_response

        return response


class CommentViewSet(viewsets.ModelViewSet):
    queryset = models.Comment.objects.all()
    serializer_class = serializers.CommentSerializer


class CommentLikeViewSet(viewsets.ModelViewSet):
    queryset = models.Like.objects.all()
    serializer_class = serializers.CommentLikeSerializer


class PostLikeViewSet(viewsets.ModelViewSet):
    queryset = models.Like.objects.all()
    serializer_class = serializers.PostLikeSerializer
