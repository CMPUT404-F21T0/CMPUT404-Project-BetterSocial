from .forms import CommentCreationForm, PostCreationForm
from django.db.models import Q
from django.views import generic
from django.contrib.contenttypes.models import ContentType as DjangoContentType
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
    fields = ['title', 'description', 'content', 'visibility', 'image_content']

    def get_success_url(self):
        return reverse_lazy('bettersocial:article_details', kwargs = { 'pk': self.kwargs['pk'] })


@method_decorator(login_required, name = 'dispatch')
class DeletePostView(generic.DeleteView):
    model = Post
    template_name = 'bettersocial/delete_post.html'
    success_url = reverse_lazy('bettersocial:index')

    # TODO: Not sure if this is the proper way to query all users / users post in db
    # using this to test clicking through different profiles it should be changed
    def users(self):
        return User.objects.all()


@method_decorator(login_required, name = 'dispatch')
class ProfileView(generic.base.TemplateView):
    model = Author
    template_name = 'bettersocial/profile.html'
    context_object_name = "current_user"

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        # author is the owner of the page we're looking at
        # user is the logged in user
        author_uuid = self.kwargs['uuid']
        author = Author.objects.filter(uuid = author_uuid).prefetch_related('post_set').get()
        context['author'] = author
        user_uuid = self.request.user.author.uuid

        if author_uuid == user_uuid:
            context['posts'] = author.post_set.all()
        else:
            context['author_following_user'] = Following.objects.filter(author = author_uuid, following_uuid = user_uuid)
            context['user_following_author'] = Following.objects.filter(author = user_uuid, following_uuid = author_uuid)

            # TODO: Might only need to have Public posts to be queried or publick and friends posts?
            context['posts'] = Post.objects.filter(
                (Q(visibility = Post.Visibility.PUBLIC) & Q(author__uuid = author_uuid)) |
                (Q(visibility = Post.Visibility.FRIENDS) & Q(author__follower__follower_uuid = user_uuid) & Q(author__following__following_uuid = user_uuid)) |
                (Q(visibility = Post.Visibility.PRIVATE) & Q(recipient_uuid = user_uuid))).order_by('-published')

        return context


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
        obj.author = Author(self.request.user.author.uuid, self.request.user)  # Automatically Put the current user as the author
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
    def form_valid(self, form):
        form.instance.post_id = self.kwargs['pk']
        '''
        form = CommentCreationForm(initial={'author_uuid': self.request.user.author.uuid})
        '''
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('bettersocial:article_details', kwargs = { 'pk': self.kwargs['pk'] })


@method_decorator(login_required, name = 'dispatch')
class InboxView(generic.ListView):
    model = Inbox
    template_name = 'bettersocial/inbox.html'
    context_object_name = 'inbox_items'

    def get_queryset(self):
        """Return all inbox items."""
        content_type = DjangoContentType.objects.get_for_model(model = Follower)
        return Inbox.objects.filter(Q(dj_content_type = content_type))


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


@method_decorator(login_required, name = 'dispatch')
class FollowersView(generic.TemplateView):
    template_name = 'bettersocial/friends.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Different way to get author than normal. This is because we want to utilize the prefetch_related optimization. This ensures that the queries following_set.all() and follower_set.all() are preloaded.
        author: Author = Author.objects.filter(user_id = self.request.user.id).prefetch_related('following_set', 'follower_set').get()

        # Save both as sets because we need to do XOR on them for follower list
        follower_set = { f.author_local for f in author.follower_set.all() }
        friends_set = { a for a in author.friends_set.all() }

        # Friend requests are any author that is NOT currently a friend and ALSO follows the current author
        context['friend_request_list'] = follower_set ^ friends_set
        context['friends_list'] = friends_set

        return context
