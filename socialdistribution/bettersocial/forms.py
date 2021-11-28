import base64

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.forms import ModelForm, ImageField

from .models import Comment, Post, ContentType


class PostCreationForm(ModelForm):
    image = ImageField()

    def save(self, commit = True):
        instance: Post = super().save(commit)
        image: InMemoryUploadedFile = self.cleaned_data['image']

        if self.cleaned_data['content_type'] in (ContentType.IMAGE_PNG, ContentType.IMAGE_JPEG):
            instance.content = base64.b64encode(image.file.read()).decode()

        return instance

    class Meta:
        model = Post

        # More fields can be added
        fields = [
            'title',
            'content_type',
            'description',
            'content',
            'visibility',
            'categories',
            'unlisted',
            'recipient_uuid'
        ]


class CommentCreationForm(ModelForm):
    class Meta:
        model = Comment

        # More fields can be added
        fields = ['author_uuid',
                  'comment']
