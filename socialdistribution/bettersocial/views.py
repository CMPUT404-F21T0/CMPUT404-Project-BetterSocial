from .forms import CommentCreationForm, PostCreationForm

from django.db.models import Q
from django.views import generic
from django.contrib.auth.models import User
from django.urls import reverse, reverse_lazy
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required

from bettersocial.models import Author, Follower, Following, Inbox, Post, Comment


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
    fields = ['title', 'description', 'visibility', 'header_image']
    
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

    # Changes require in the future
    # The form itself has error message for the user if he / she does it incorrectly.
    def post(self, request):
        form = PostCreationForm(request.POST, request.FILES)

        obj = form.save(commit = False)
        obj.author = Author(self.request.user.author.uuid, self.request.user)    # Automatically Put the current user as the author
        obj.save()

        return redirect('bettersocial:index')

@method_decorator(login_required, name = 'dispatch')
class AddCommentView(generic.CreateView):
    model = Comment
    form_class = CommentCreationForm    
    template_name = 'bettersocial/add_comment.html'

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
    
@method_decorator(login_required, name = 'dispatch')
class InboxView(generic.base.TemplateView):
    model = Inbox     # should the model be this??
    template_name = 'bettersocial/inbox.html'
    context_object_name = 'inbox_items'

    def get_queryset(self):
        """Return all inbox items."""
        return Inbox.objects.order_by('-published')

@method_decorator(login_required, name = 'dispatch')
class StreamView(generic.ListView):
    model = Post
    template_name = 'bettersocial/stream.html'
    context_object_name = 'stream_items'
    
    def get_queryset(self):
        """Return all post objects."""
        author_uuid = self.request.user.author.uuid
        return Post.objects.filter(
            (Q(visibility = Post.Visibility.PUBLIC)) | 
            (Q(visibility = Post.Visibility.FRIENDS) & Q(author__follower__follower_uuid = author_uuid) & Q(author__following__following_uuid = author_uuid)) | 
            (Q(visibility = Post.Visibility.PRIVATE) & Q(recipient_uuid = author_uuid))).order_by('-published')
