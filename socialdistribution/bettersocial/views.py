from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils.decorators import method_decorator
from django.views import generic

from bettersocial.models import Author, Inbox, Post


class IndexView(generic.base.TemplateView):
    template_name = 'bettersocial/index.html'
    context_object_name = 'user_list'

    # TODO: Not sure if this is the proper way to query all users / users post in db
    def users(self):
        return User.objects.all()


@method_decorator(login_required, name = 'dispatch')
class ProfileView(generic.base.TemplateView):
    template_name = 'bettersocial/profile.html'


@method_decorator(login_required, name = 'dispatch')
class InboxView(generic.base.TemplateView):
    model = Inbox  # should the model be this??
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
