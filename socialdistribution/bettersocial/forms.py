from .models import Comment, Post
from django.forms import ModelForm

class PostCreationForm(ModelForm):

    class Meta:
        model = Post

        # More fields can be added
        fields = ['title',
                  'description', 
                  'content',
                  'visibility',
                  'header_image']

class CommentCreationForm(ModelForm):

    class Meta:
        model = Comment

        # More fields can be added
        fields = ['author_uuid',
                  'author_username',
                  'comment']

