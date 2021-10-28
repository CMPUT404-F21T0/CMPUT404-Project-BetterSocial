from .models import Comment, Post
from django.forms import ModelForm

class PostCreationForm(ModelForm):

    class Meta:
        model = Post

        # Fields can be added
        fields = ['title',
                  'content', 
                  'visibility']

class CommentCreationForm(ModelForm):

    class Meta:
        model = Comment

        # Fields can be added
        fields = ['author_uuid',
                  'author_username',
                  'comment']