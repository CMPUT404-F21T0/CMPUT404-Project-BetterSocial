from typing import Dict, List

from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import empty
from rest_framework.reverse import reverse
from rest_framework_nested import serializers as nested_serializers

from api.helpers import uuid_helpers
from bettersocial.models import *


class AuthorSerializer(serializers.ModelSerializer):
    type = models.CharField(max_length = 32)

    id = serializers.HyperlinkedIdentityField(
        view_name = 'api:author-detail',
    )

    url = serializers.Field(default = None)

    host = serializers.SerializerMethodField(
        method_name = 'get_host'
    )

    displayName = serializers.SerializerMethodField(
        method_name = 'get_name'
    )

    profileImage = serializers.Field(default = None)

    # Not required, but for convenience
    posts = serializers.HyperlinkedIdentityField(
        view_name = 'api:post-list',
        lookup_url_kwarg = 'author_pk',
    )

    def get_host(self, instance: Author):
        return reverse('api:api-root', request = self.context['request'])

    def get_name(self, instance: Author):
        # TODO: 2021-10-25 simplify
        return instance.display_name

    def to_representation(self, instance):
        json = super().to_representation(instance)

        json['id'] = uuid_helpers.remove_uuid_dashes(json['id'])

        json['url'] = json['id']

        return json

    class Meta:
        model = Author
        fields = [
            'type',
            'id',
            'url',
            'host',
            'displayName',
            'github',
            'profileImage',
            'posts'
        ]
        extra_kwargs = {
            'github': {
                'source': 'github_url'
            }
        }


class CommentSerializer(serializers.ModelSerializer):
    type = models.CharField(max_length = 32)

    id = nested_serializers.NestedHyperlinkedIdentityField(
        view_name = 'api:comment-detail',
        parent_lookup_kwargs = {
            'post_pk': 'post__pk',
            'author_pk': 'post__author__pk',
        }
    )

    author = serializers.SerializerMethodField(
        method_name = 'get_author'
    )

    def get_author(self, instance: Comment):
        # TODO: 2021-11-22 refactor for remote authors
        return AuthorSerializer(instance = instance.author_local, context = self.context, read_only = True).data

    def to_representation(self, instance):
        json = super().to_representation(instance)

        json['id'] = uuid_helpers.remove_uuid_dashes(json['id'])

        return json

    class Meta:
        model = Comment
        fields = [
            'type',
            'author',
            'comment',
            'contentType',
            'published',
            'id',
        ]
        extra_kwargs = {
            'contentType': {
                'source': 'content_type',
            }
        }


class PostSerializer(serializers.ModelSerializer):
    id = nested_serializers.NestedHyperlinkedIdentityField(
        view_name = 'api:post-detail',
        parent_lookup_kwargs = { 'author_pk': 'author__pk' }
    )

    type = models.CharField(max_length = 32)

    count = serializers.IntegerField(
        source = 'comments.count',
        read_only = True,
    )

    comments = nested_serializers.NestedHyperlinkedIdentityField(
        view_name = 'api:comment-list',
        read_only = True,
        lookup_url_kwarg = 'post_pk',
        parent_lookup_kwargs = {
            'author_pk': 'author__pk',
        }
    )

    author = AuthorSerializer(read_only = True)

    commentsSrc = serializers.SerializerMethodField(
        method_name = 'get_comments'
    )

    def get_comments(self, instance: Post):
        # Gotta hardcode this stuff because there's no way to get the "list representation" without a circular import
        return {
            'type': 'comments',
            'page': 1,
            'size': 5,
            'post': None,  # Both to be filled in to_representation because we can't reference an existing field here, apparently.
            'id': None,
            'comments': CommentSerializer(instance.comments.order_by('-published')[:5], context = self.context, many = True).data,
        }

    published = serializers.DateTimeField(format = 'iso-8601')

    def to_representation(self, instance):
        json = super().to_representation(instance)

        json['id'] = uuid_helpers.remove_uuid_dashes(json['id'])
        json['comments'] = uuid_helpers.remove_uuid_dashes(json['comments'])

        # Set defaults for source and origin, if they don't exist. This shouldn't really happen but just in case
        if json['source'] is None:
            json['source'] = json['id']

        if json['origin'] is None:
            json['origin'] = json['id']

        # Fill in repeated data because that's the spec
        json['commentsSrc']['post'] = json['id']
        json['commentsSrc']['id'] = json['comments']

        return json

    class Meta:
        model = Post
        fields = [
            'type',
            'title',
            'id',
            'source',
            'origin',
            'description',
            'contentType',
            'content',
            'author',
            'categories',
            'count',
            'comments',
            'commentsSrc',
            'published',
            'visibility',
            'unlisted'
        ]
        extra_kwargs = {
            'contentType': {
                'source': 'content_type',
            }
        }


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
        return instance.author_local

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


class InboxItemSerializer(serializers.ModelSerializer):
    """The ModelSerializer part of this is only for the GET part -- POST is kind of custom"""

    def __init__(self, instance = None, data = empty, **kwargs):
        super().__init__(instance, data, **kwargs)

        self.types = {
            'post': {
                'model': Post,
                'validator': self._validate_post
            },
            'comment': {
                'model': Comment,
                'validator': self._validate_comment
            },
            'like': {
                'model': Like,
                'validator': self._validate_like
            },
            'follow': {
                'model': Follower,
                'validator': self._validate_follower
            },
        }

    def create(self, validated_data):
        # We have to access the raw request since DRF blows any fields that are not part of the Model
        data: Dict = self.context['request'].data

        inbox_item = InboxItem.objects.create(
            author_id = self.context['author_id'],
            dj_content_type = DjangoContentType.objects.get_for_model(model = self.types[data['type']]['model']),
            inbox_object = data
        )

        return inbox_item

    def validate(self, attrs):

        # We have to access the raw request since DRF blows any fields that are not part of the Model
        data: Dict = self.context['request'].data

        # Make sure that type is there
        self._validate_required(data, ['type'])

        # Fix type field
        data['type'] = data['type'].strip().lower()

        if data['type'] not in self.types.keys():
            raise ValidationError({ 'type': f'type must be one of {{{", ".join(self.types.keys())}}}!' })

        # Access the validator for that type and call it. It might change request.data somehow
        self.types[data['type']]['validator'](data)

        # return attrs, not data, to make DRF happy
        return attrs

    def _validate_required(self, data: Dict, required_fields: List):
        for field in required_fields:
            if field not in data:
                raise ValidationError({ field: 'This field is required!' })

    def _validate_post(self, data: Dict):

        # Don't really care about the other fields
        self._validate_required(data, [
            'title',
            'id',
            'description',
            'contentType',
            'content',
            'author',
            'visibility'
        ])

        return data

    def _validate_comment(self, data: Dict):
        return data

    def _validate_like(self, data: Dict):
        return data

    def _validate_follower(self, data: Dict):

        # Don't really care about the other fields
        self._validate_required(data, [
            'actor',
            'object',
        ])

        if not isinstance(data['actor'], dict):
            raise ValidationError({ 'actor': 'This field must be an object containing an author!' })

        # Supposedly our author
        if not isinstance(data['object'], dict):
            raise ValidationError({ 'object': 'This field must be an object containing an author!' })

        self._validate_required(data['actor'], [
            'type',
            'id',
            'host'
        ])

        # Supposedly our author
        self._validate_required(data['object'], [
            'type',
            'id',
            'host'
        ])

        author_uuid = uuid_helpers.extract_author_uuid_from_id(data['object']['id'])

        if author_uuid is None:
            raise ValidationError({ 'object': 'The author\'s `id` field must have a valid author UUID!' })

        # Make sure the target is our author
        if UUID(self.context['author_id']) != author_uuid:
            raise ValidationError({ 'object': 'The author\'s `id` field must match the author you\'re sending it to!' })

        return data

    def to_representation(self, instance):
        json = super().to_representation(instance)

        # Flatten representation
        json = json['inbox_object']

        return json

    class Meta:
        model = InboxItem
        fields = ['inbox_object']
