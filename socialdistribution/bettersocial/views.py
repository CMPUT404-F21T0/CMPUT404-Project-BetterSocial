from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType as DjangoContentType
from django.db import models
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
class InboxView(generic.ListView):
    model = Inbox
    template_name = 'bettersocial/inbox.html'
    context_object_name = 'inbox_items'

    def get_queryset(self):
        """Return all inbox items."""
        content_type = DjangoContentType.objects.get_for_model(model = Post)
        return Inbox.objects.filter(Q(dj_content_type=content_type))

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
