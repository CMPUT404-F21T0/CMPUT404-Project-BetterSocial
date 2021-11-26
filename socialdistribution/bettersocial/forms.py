from .models import Comment, Post
from django.forms import ModelForm

class PostCreationForm(ModelForm):

    class Meta:
        model = Post

        # More fields can be added
        fields = ['title', 
                  'content_type',
                  'description', 
                  'content',
                  'visibility',
                  'image_content',
                  'categories',
                  'unlisted',
                  'recipient_uuid']

class CommentCreationForm(ModelForm):

    class Meta:
        model = Comment

        # More fields can be added
        fields = ['author_uuid',
                  'comment']

