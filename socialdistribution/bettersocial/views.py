from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from django.views import generic
from django.db.models import Q

from bettersocial.models import Author, Follower, Following, Inbox, Post


class IndexView(generic.base.TemplateView):
    template_name = 'bettersocial/index.html'


@method_decorator(login_required, name = 'dispatch')
class ProfileView(generic.base.TemplateView):
    template_name = 'bettersocial/profile.html'

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
        author = self.request.user.author.uuid
        return Post.objects.filter(
            (Q(visibility = Post.Visibility.PUBLIC)) | 
            (Q(visibility = Post.Visibility.FRIENDS) & Q(author__follower__follower_uuid = author) & Q(author__following__following_uuid = author)) | 
            (Q(visibility = Post.Visibility.PRIVATE) & Q(recipient_uuid = author))).order_by('-published')
