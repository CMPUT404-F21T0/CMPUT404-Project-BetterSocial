import base64

from django.core.files.uploadedfile import InMemoryUploadedFile
from django.forms import ModelForm, ImageField, widgets
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
from django import forms
from django.forms.forms import Form

from .models import Author, Comment, Post, ContentType


class PostCreationForm(ModelForm):
    image = ImageField(required=False)

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
        
        '''
        # TODO : Probably need to include remote authors in the select options at some point
        ALL_LOCAL_AUTHORS = Author.objects.all()
        AUTHOR_CHOICES = [((""),("-----"))]
        for x in ALL_LOCAL_AUTHORS:
            AUTHOR_CHOICES.append((x.uuid, x.user))
        '''

        widgets = {
            'recipient_uuid': forms.TextInput(attrs={'onChange': "validate()"}),
            'visibility': forms.Select(attrs={'onChange': "validate()"}),
            'unlisted': forms.CheckboxInput(attrs={'onChange': "validate()"}),
        }

class CommentCreationForm(ModelForm):
    class Meta:
        model = Comment

        # More fields can be added
        fields = [
            'comment'
        ]

class EditProfileForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['username',
                  'first_name', 
                  'last_name', 
                  'email', 
                  'password'] 
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = ""
        self.fields['password'].help_text = '<a style="color:red" href=\"../password/\">Click this to change password</a> '
