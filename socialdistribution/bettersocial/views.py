from django.db.models import query
from django.http.response import Http404
from .models import Comment, Post, Author
from .forms import CommentCreationForm, PostCreationForm

from django.views import generic
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse


class IndexView(generic.ListView):
    model = Post
    template_name = 'bettersocial/index.html'

@method_decorator(login_required, name = 'dispatch')
class ArticleDetailView(generic.DetailView):
    model = Post
    template_name = 'bettersocial/article_details.html'

@method_decorator(login_required, name = 'dispatch')
class UpdatePostView(generic.UpdateView):
    model = Post
    template_name = 'bettersocial/edit_post.html'
    fields = ['title', 'content', 'visibility']
    def get_success_url(self):
        return reverse_lazy('bettersocial:article_details', kwargs={'pk': self.kwargs['pk']})

@method_decorator(login_required, name = 'dispatch')
class DeletePostView(generic.DeleteView):
    model = Post
    template_name = 'bettersocial/delete_post.html'
    success_url = reverse_lazy('bettersocial:index')

@method_decorator(login_required, name = 'dispatch')
class ProfileView(generic.base.TemplateView):
    template_name = 'bettersocial/profile.html'

@method_decorator(login_required, name = 'dispatch')
class AddPostView(generic.CreateView):
    model = Post
    form_class = PostCreationForm
    template_name = 'bettersocial/postapost.html'
    success_url = reverse_lazy('bettersocial:index')

    
    # Override the POST Method
    # The form itself has error message for the user if he / she does it incorrectly.
    def post(self, request):
        form = PostCreationForm(request.POST)
        obj = form.save(commit = False)
        obj.author = Author(self.request.user.author.uuid, self.request.user)   # Automatically Put the current user as the author
        obj.save()

        return render(request, 'bettersocial/profile.html', {'user': request.user}) # Going back to the profile page / home page currently

@method_decorator(login_required, name = 'dispatch')
class AddCommentView(generic.CreateView):
    model = Comment
    form_class = CommentCreationForm    
    template_name = 'bettersocial/add_comment.html'
    success_url = reverse_lazy('bettersocial:index')

    # Presets the author uuid to the currently logged in user
    # https://stackoverflow.com/questions/54153528/how-to-populate-existing-html-form-with-django-updateview
    def get_initial(self):
        initial = super().get_initial()
        initial['author_uuid'] = self.request.user.author.uuid
        initial['author_username'] = self.request.user.author.user
        return initial

    # Injections the proper post id for the comment
    def form_valid (self, form):
        form.instance.post_id = self.kwargs['pk']
        '''
        form = CommentCreationForm(initial={'author_uuid': self.request.user.author.uuid})
        '''
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('bettersocial:article_details', kwargs={'pk': self.kwargs['pk']})
    


        


    



