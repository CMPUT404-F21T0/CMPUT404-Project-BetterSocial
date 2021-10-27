from .models import Post
from django.forms import ModelForm

class PostCreationForm(ModelForm):

    class Meta:
        model = Post

        # Fields can be added
        fields = ['title',
                  'content', 
                  'visibility']
