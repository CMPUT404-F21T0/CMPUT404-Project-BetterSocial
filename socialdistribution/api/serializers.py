from rest_framework import serializers
from rest_framework.reverse import reverse
from rest_framework_nested import serializers as nested_serializers

from bettersocial.models import *


class PostSerializer(serializers.ModelSerializer):
    id = nested_serializers.NestedHyperlinkedIdentityField(
        view_name = 'api:post-detail',
        parent_lookup_kwargs = { 'author_pk': 'author__pk' }
    )

    type = models.CharField(max_length = 32)

    # count = serializers.IntegerField(
    #     source = 'comment_set.count',
    #     read_only = True,
    # )

    author = nested_serializers.NestedHyperlinkedRelatedField(
        view_name = 'api:author-detail',
        read_only = True,
        parent_lookup_kwargs = { 'author_pk': 'author__pk' }
    )

    # commentsSrc = serializers.SerializerMethodField(
    #     method_name = 'get_commentsSrc'
    # )

    def get_commentsSrc(self, instance: Post):
        return {
            'type': 'comments',
            'page': 1,
            'size': 5,
            'post': None,
            'id': None,
            'comments': CommentSerializer(instance.comment_set.order_by('-published')[:5], context = self.context, many = True).data,
        }

    class Meta:
        model = Post
        fields = [
            'type',
            'title',
            'id',
            # 'source',
            # 'origin',
            # 'description',
            # 'contentType',
            # 'content',
            'author',
            # 'categories',
            # 'count',
            # 'comments',
            # 'commentsSrc',
            # 'published',
            # 'visibility',
            # 'unlisted'
        ]
        extra_kwargs = {
            'contentType': {
                'source': 'content_type',
            },
        }


class AuthorSerializer(serializers.ModelSerializer):
    type = models.CharField(max_length = 32)

    id = serializers.HyperlinkedIdentityField(
        view_name = 'api:author-detail',
    )

    host = serializers.SerializerMethodField(
        method_name = 'get_host'
    )

    displayName = serializers.SerializerMethodField(
        method_name = 'get_name'
    )

    # posts = serializers.HyperlinkedIdentityField(
    #     view_name = 'api:post-list',
    #     lookup_url_kwarg = 'author_pk',
    # )

    def get_host(self, instance: Author):
        return reverse('bettersocial:index', request = self.context['request'])

    def get_name(self, instance: Author):
        # TODO: 2021-10-25 simplify
        return instance.display_name

    def to_representation(self, instance):
        json = super().to_representation(instance)

        json['url'] = json['id']

        return json

    class Meta:
        model = Author
        fields = [
            'type',
            'id',
            'host',
            'displayName',
            'github_url',
            # 'profileImage',
        ]
        # extra_kwargs = {
        # }


class CommentSerializer(serializers.ModelSerializer):
    type = models.CharField(max_length = 32)

    id = nested_serializers.NestedHyperlinkedIdentityField(
        view_name = 'api:comment-detail',
        parent_lookup_kwargs = {
            'post_pk': 'post__pk',
            'author_pk': 'post__author__pk',
        }
    )

    # id = serializers.HyperlinkedIdentityField(
    #     view_name = 'api:comment-detail',
    #     read_only = True,
    # )

    # post = nested_serializers.NestedHyperlinkedRelatedField(
    #     view_name = 'api:posts-detail',
    #     read_only = True,
    # )

    class Meta:
        model = Comment
        fields = '__all__'


class BaseLikeSerializer(serializers.ModelSerializer):
    summary = serializers.SerializerMethodField(
        method_name = 'get_summary'
    )

    type = models.CharField(max_length = 32)

    author = serializers.SerializerMethodField(
        method_name = 'get_author'
    )

    # TODO: 2021-10-25 refactor later for remote authors
    @staticmethod
    def helper_get_author(instance: Like) -> Author:
        return Author.objects.filter(uuid = instance.author_uuid).first()

    def get_summary(self, instance: Like):
        return f'{self.helper_get_author(instance).display_name} Likes your post'

    def get_author(self, instance: Like):
        return AuthorSerializer(self.helper_get_author(instance), context = self.context).data

    def to_representation(self, instance):
        json = super().to_representation(instance)

        json['@context'] = 'https://www.w3.org/ns/activitystreams'
        json.move_to_end('@context', last = False)

        return json

    class Meta:
        model = Like
        fields = [
            # '@context',
            'summary',
            'type',
            'author',
            # 'object',
        ]


class PostLikeSerializer(BaseLikeSerializer):
    pass


class CommentLikeSerializer(BaseLikeSerializer):
    pass
