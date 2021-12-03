from collections import OrderedDict
from uuid import UUID

from django.contrib.auth.models import User
from django.db.models import Q
from django.http.response import HttpResponseServerError
from rest_framework import viewsets, mixins, permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from api import pagination
from api import serializers
from api.helpers import uuid_helpers
from bettersocial import models
from bettersocial.models import Post, InboxItem, Node, Author, Follower
from socialdistribution.bettersocial.models import UUIDRemoteCache

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
    serializer_class = serializers.FollowerSerializer

    def get_queryset(self):
        author = models.Author.objects.filter(uuid = self.kwargs['author_pk']).get()
        return models.Follower.objects.filter(author = author).all()
    
    def retrieve(self, request, *args, **kwargs):
        '''
        GET {host_url}/author/{author_uuid}/followers/{foreign_uuid}
        
        Checks if the provided foreign_uuid is a follower of the user
        '''
        response = super().retrieve(request, *args, **kwargs)
        followers = self.get_queryset()
        foreign_uuid = kwargs['pk']
        follower_qs = followers.filter(follower_uuid=foreign_uuid)
        if follower_qs.exists():
            # get author serialize
            author_uuid = self.kwargs['author_pk']
            author_qs = Author.objects.filter(uuid = author_uuid)
            if author_qs.exists():
                author = author_qs.get()
                response.data = serializers.AuthorSerializer(author, context = { 'request': request }).data
            else:
                # remote author, GET info
                remote_node_qs = UUIDRemoteCache.objects.filter(uuid=author_uuid)
                if remote_node_qs.exists():
                    # TODO: GET it and serialize it
                    pass
                else:
                    # 
                    return HttpResponseServerError({'message': 'Follower exists locally but author cannot be found'})
        return response


    
    def list(self, request, *args, **kwargs):
        '''
        GET {host_url}/author/{author_uuid}/followers
        
        Gets list of authors who are the author_uuid's followers
        '''
        response = super().list(request, *args, **kwargs)
        response['type'] = 'followers'
        items = list()

        followers = self.get_queryset()
        for follower in followers:
            follower_author = Author.objects.filter(uuid = follower.follower_uuid)
            
            if follower_author.exists():
                items.append(serializers.AuthorSerializer(follower_author.get(),  context = { 'request': request }).data)

            # TODO: add functionality for getting remote followers

        response['items'] = items
        return Response(response)


    def update(self, request, *args, **kwargs):
        '''
        PUT {host_url}/author/{author_uuid}/followers/{foreign_uuid}

        Adds a follower (must be authenticated)
        '''
        if not isinstance(request.user, User):
            raise PermissionDenied({ 'message': "You must be authenticated as a user to get inbox items!" })

        if request.user.author.uuid != UUID(self.kwargs['author_pk']):
            raise PermissionDenied({ 'message': "You cannot get the inbox items of another user!" })

        author = Author.objects.filter(uuid = kwargs['author_pk']).get()
        foreign_uuid = kwargs['pk']

        if not Follower.objects.filter(author = author, follower_uuid = foreign_uuid):
            Follower(author = author, follower_uuid = foreign_uuid)
            return Response()
        else:
            return 

    def destroy(self, request, *args, **kwargs):
        '''
        DELETE {host_url}/author/{author_uuid}/followers/{foreign_uuid}

        Remove a follower
        '''
        foreign_uuid = kwargs['pk']
        Follower.objects.filter(follower_uuid=foreign_uuid).delete()
        return Response()


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
