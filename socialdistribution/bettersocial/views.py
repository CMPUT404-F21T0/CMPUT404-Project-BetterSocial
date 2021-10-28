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
class ProfileView(generic.ListView):
    model = Author
    template_name = 'bettersocial/profile.html'
    context_object_name = "current_user"

    def get_context_data(self, **kwargs):
        author_uuid = self.kwargs["uuid"]    
        context = super(ProfileView, self).get_context_data(**kwargs)
        # Shows all the posts of the current logged in user
        # not sure how to handle a user viewing a different user's profile
        # TODO: fix this so it queries public/friend post
        context['posts'] = Post.objects.filter(author__uuid = author_uuid)
        return context

    def get_queryset(self):
        uuid = self.kwargs["uuid"]        
        return Author.objects.get(uuid = uuid)

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
