from .models import Post, Author
from .forms import PostCreationForm

from django.views import generic
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse


class IndexView(generic.base.TemplateView):
    template_name = 'bettersocial/index.html'


@method_decorator(login_required, name = 'dispatch')
class ProfileView(generic.base.TemplateView):
    template_name = 'bettersocial/profile.html'

@method_decorator(login_required, name = 'dispatch')
class AddPostView(generic.CreateView):
    model = Post
    form_class = PostCreationForm
    template_name = 'bettersocial/postapost.html'

    # Override the POST Method
    # The form itself has error message for the user if he / she does it incorrectly.
    def post(self, request):
        form = PostCreationForm(request.POST)

        obj = form.save(commit = False)
        obj.author = Author(self.request.user.author.uuid, self.request.user)   # Automatically Put the current user as the author
        obj.save()

        return render(request, 'bettersocial/profile.html', {'user': request.user}) # Going back to the profile page / home page currently
       
        
        


    



