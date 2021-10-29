from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views import generic
from django.db.models import Q

from bettersocial.models import Author, Follower, Following, Inbox, Post

class IndexView(generic.base.TemplateView):
    template_name = 'bettersocial/index.html'
    context_object_name = 'user_list'

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
            context['author_following_user'] = Following.objects.filter(author=author_uuid, following_uuid=user_uuid)
            context['user_following_author']= Following.objects.filter(author=user_uuid, following_uuid=author_uuid)

            # TODO: Might only need to have Public posts to be queried or publick and friends posts?
            context['posts'] = Post.objects.filter(
                (Q(visibility = Post.Visibility.PUBLIC) & Q(author__uuid = author_uuid)) | 
                (Q(visibility = Post.Visibility.FRIENDS) & Q(author__follower__follower_uuid = user_uuid) & Q(author__following__following_uuid = user_uuid)) | 
                (Q(visibility = Post.Visibility.PRIVATE) & Q(recipient_uuid = user_uuid))).order_by('-published')
        
        return context

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
