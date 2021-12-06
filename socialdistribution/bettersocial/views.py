import json

import requests
import yarl
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.views import PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.http import HttpResponseNotFound, HttpRequest, HttpResponseBadRequest
from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views import generic
from requests.auth import HTTPBasicAuth

from api.helpers import author_helpers, uuid_helpers, remote_helpers
from api.serializers import PostSerializer, CommentSerializer, AuthorSerializer
from bettersocial.models import Author, Follower, Following, InboxItem, Post, Comment, Node
from .forms import CommentCreationForm, PostCreationForm, EditProfileForm


@method_decorator(login_required, name = 'dispatch')
class ArticleDetailView(generic.TemplateView):
    template_name = 'bettersocial/article_details.html'

    def get(self, request: HttpRequest, *args, **kwargs):

        context = self.get_context_data(**kwargs)

        if context.get('post') is None:
            return HttpResponseNotFound("The post could not be found!")
        else:
            return self.render_to_response(context)

    def _find_post(self, context, **kwargs):
        """Returns the JSON of the post, if found, and its comments, if applicable"""

        # First try to find the post locally
        post_qs = Post.objects.filter(pk = self.kwargs['pk'])

        if post_qs.exists():
            post = post_qs.get()
            comments = post.comments.order_by('-published').all()

            return PostSerializer(post, context = { 'request': self.request }).data, \
                   CommentSerializer(comments, context = { 'request': self.request }, many = True).data

        # If that fails, try to find it in the author's inbox (maybe it's private but on here)
        inbox_items = InboxItem.objects.filter(author = self.request.user.author, inbox_object__iregex = '"type": "post"').all()

        for item in inbox_items:
            if uuid_helpers.extract_post_uuid_from_id(item.inbox_object['id']) == self.kwargs['pk']:

                # IF the post is public, we should get the most recent version
                if item.inbox_object['visibility'].upper() == Post.Visibility.PUBLIC.value.upper():
                    node = Node.objects.filter(host__contains = item.inbox_object['author']['host']).get()

                    post_response = requests.get(
                        item.inbox_object['url'],
                        headers = { 'Accept': 'application/json' },
                        auth = HTTPBasicAuth(node.node_username, node.node_password)
                    )

                    post_response.raise_for_status()

                    comments_response = requests.get(
                        item.inbox_object['comments'],
                        params = { 'size': 100 },
                        headers = { 'Accept': 'application/json' },
                        auth = HTTPBasicAuth(node.node_username, node.node_password)
                    )

                    comments_response.raise_for_status()

                    if post_response.ok:
                        return post_response.json(), comments_response.json()['comments'] if comments_response.ok else []

                else:
                    return item.inbox_object

        # All else fails, try to find it remotely (this must be a public post)

        pass

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        post, comments = self._find_post(context, **kwargs)

        if post is None:
            return context

        # Make post UUID available in _uuid
        post['_uuid'] = uuid_helpers.extract_post_uuid_from_id(post['id']).hex

        # Make author UUID available in author._uuid
        post['author']['_uuid'] = uuid_helpers.extract_author_uuid_from_id(post['author']['id']).hex

        # post_uuid = self.kwargs['pk']
        # post = Post.objects.get(pk = post_uuid)
        # author_uuid = post.author.uuid
        # user_uuid = self.request.user.author.uuid
        #
        # if user_uuid == author_uuid:
        #     context["comments"] = post.comments.all()
        #     return context
        #
        # # finding author's friends (excluding the user) in order to hide author's friend's comments from user
        # author_following = Following.objects.filter(Q(author = author_uuid) & ~Q(following_uuid = user_uuid)).values_list("following_uuid")
        # author_followers = Following.objects.filter(Q(following_uuid = author_uuid) & ~Q(author = user_uuid)).values_list("author__uuid")
        # friends_to_hide = author_following.intersection(author_followers)
        # context["comments"] = (post.comments.all().exclude(author_uuid__in = friends_to_hide))

        context['post'] = json.dumps(post)
        context['comments'] = json.dumps(comments)

        return context


@method_decorator(login_required, name = 'dispatch')
class UpdatePostView(generic.UpdateView):
    model = Post
    template_name = 'bettersocial/edit_post.html'
    form_class = PostCreationForm

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        post_qs = Post.objects.filter(uuid = self.kwargs['pk'])

        if post_qs.exists() and post_qs.get().author.uuid != request.user.author.uuid:
            raise PermissionDenied('You may not edit the post of another user!')

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('bettersocial:article_details', kwargs = { 'pk': self.kwargs['pk'] })


@method_decorator(login_required, name = 'dispatch')
class DeletePostView(generic.DeleteView):
    model = Post
    template_name = 'bettersocial/delete_post.html'
    success_url = reverse_lazy('bettersocial:index')

    def dispatch(self, request: HttpRequest, *args, **kwargs):
        post_qs = Post.objects.filter(uuid = self.kwargs['pk'])

        if post_qs.exists() and post_qs.get().author.uuid != request.user.author.uuid:
            raise PermissionDenied('You may not delete the post of another user!')

        return super().dispatch(request, *args, **kwargs)


@method_decorator(login_required, name = 'dispatch')
class ProfileView(generic.base.TemplateView):
    model = Author
    template_name = 'bettersocial/profile.html'
    context_object_name = "current_user"

    def get(self, request, *args, **kwargs):
        # try:
        #     location = self.request.GET['location']
        #     host = self.request.GET['host']

        #     # JavaScript moment
        #     if location == 'undefined' or host == 'undefined':
        #         return HttpResponseBadRequest('both query parameters must be defined!')

        # except KeyError:
        #     return HttpResponseBadRequest('you must the location and host query parameters in the request!')

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ProfileView, self).get_context_data(**kwargs)
        # author is the owner of the page we're looking at
        # user is the logged in user
        author_uuid = context['uuid']
        user_uuid = self.request.user.author.uuid

        author_qs = Author.objects.filter(uuid = author_uuid)
        if author_qs.exists():
            context['author'] = AuthorSerializer(author_qs.get(), context = {'request': self.request}).data

            # TODO: Might only need to have Public posts to be queried or publick and friends posts?
            context['posts'] = Post.objects.filter(
                (Q(visibility = Post.Visibility.PUBLIC) & Q(author__uuid = author_uuid)) |
                (Q(visibility = Post.Visibility.FRIENDS) & Q(author__follower__follower_uuid = user_uuid) & Q(author__following__following_uuid = user_uuid)) |
                (Q(visibility = Post.Visibility.PRIVATE) & Q(recipient_uuid = user_uuid))).distinct().order_by('-published')
        else:
            context['author'] = remote_helpers.find_remote_author(author_uuid)
            
            # get authors posts
            node = remote_helpers.get_node_of_uuid((author_uuid))
            if not node:
                node = Node.objects.filter().get(host__contains = self.request.GET['host']).get()

            url = (yarl.URL(node.host) / node.prefix / 'author' / author_uuid / '').human_repr()
            author_posts_resp = requests.get(
                url,
                headers = {'Accept': 'application/json'},
                auth = HTTPBasicAuth(node.node_username, node.node_password)    # Shouldn't need but in case
            )

            author_posts_resp.raise_for_status()

            if author_posts_resp.ok:
                context['posts'] = author_posts_resp.json()

        # Get follow button actions
        if author_uuid == user_uuid:
            author = Author.objects.filter(uuid = author_uuid).prefetch_related('post_set').get()
            context['posts'] = author.post_set.all().order_by('-published')
        else:
            context['author_following_user'] = bool(Following.objects.filter(author = author_uuid, following_uuid = user_uuid))
            context['user_following_author'] = bool(Following.objects.filter(author = user_uuid, following_uuid = author_uuid))

        return context

# CODE REFERENCED: https://stackoverflow.com/questions/54187625/django-on-button-click-call-function-view
@method_decorator(login_required, name = 'dispatch')
class ProfileActionView(generic.View):
    def post(self, request, uuid, action, *args, **kwargs):
        author = Author.objects.filter(uuid = request.user.author.uuid).get()
        if action == 'follow':
            Following.objects.create(following_uuid = uuid, author = author)
            Follower.objects.create(follower_uuid = author.uuid, author_id = uuid)
        elif action == 'unfollow':
            Following.objects.filter(following_uuid = uuid, author = author).delete()
            Follower.objects.filter(follower_uuid = author.uuid, author_id = uuid).delete()

        # If target user is not local, need to send api request for follow req + unfollow
        if not Author.objects.filter(uuid = uuid).exists():
            node = Node.objects.filter(host__contains = self.request.GET['host']).get()
            if action == 'follow':
                author_serialized = AuthorSerializer(author, context = { 'request': self.request }).data
                remote_author = remote_helpers.find_remote_author(uuid)
                follower_json = {
                    'type': 'Follow',
                    'summary': f'{author_serialized.displayName} wants to follow user at {uuid}',
                    'actor': {
                        'type': 'author',
                        'id': author_serialized.id,
                        'url': author_serialized.url,
                        'host': author_serialized.host,
                        'displayName': author_serialized.displayName,
                        'github': '',
                        'profileImage': ''
                    },
                    'object': {
                        'type': 'author',
                        'id': remote_author['id'],
                        'url': remote_author['url'],
                        'host': remote_author['host'],
                        'displayName': remote_author['displayName'],
                        'github': remote_author['github'],
                        'profileImage': remote_author['profileimage']
                    }
                }

                # TODO: need foreign author uuid with remote host url
                url = (yarl.URL(node.host) / node.prefix / 'author' / author.uuid / 'inbox' / '').human_repr()
                response = requests.post(
                    url,
                    headers = { 'Accept': 'application/json' },
                    auth = HTTPBasicAuth(node.node_username, node.node_password),
                    json = follower_json
                )

                response.raise_for_status()

                if response.ok:
                    print(response.content)
            if action == 'unfollow':
                pass

        return HttpResponseRedirect(reverse('bettersocial:profile', args = (uuid,)))


@method_decorator(login_required, name = 'dispatch')
class AddPostView(generic.CreateView):
    model = Post
    form_class = PostCreationForm
    template_name = 'bettersocial/postapost.html'

    def get_success_url(self):
        if 'done' in self.request.POST:
            url = reverse_lazy('bettersocial:index')
        return url

    # Changes require in the future
    # The form itself has error message for the user if he / she does it incorrectly.
    def post(self, request, **kwargs):
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

    def get(self, request, *args, **kwargs):

        try:
            location = self.request.GET['location']
            host = self.request.GET['host']

            # JavaScript moment
            if location == 'undefined' or host == 'undefined':
                return HttpResponseBadRequest('both query parameters must be defined!')

        except KeyError:
            return HttpResponseBadRequest('you must the location and host query parameters in the request!')

        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):

        form = self.get_form()

        if form.is_valid():

            post_id = uuid_helpers.extract_post_uuid_from_id(self.request.GET['location'])
            if Post.objects.filter(pk = post_id).exists():
                return super().post(request, *args, **kwargs)
            else:
                # Post must be remote, sending to url
                node = Node.objects.filter(host__contains = self.request.GET['host']).get()

                form_comment: Comment = form.instance

                comment_json = {
                    'type': 'comment',
                    'author': AuthorSerializer(self.request.user.author, context = { 'request': self.request }).data,
                    'comment': form_comment.comment,
                    'contentType': form_comment.content_type,
                }

                response = requests.post(
                    yarl.URL(self.request.GET['location']).human_repr(),
                    headers = { 'Accept': 'application/json' },
                    auth = HTTPBasicAuth(node.node_username, node.node_password),
                    json = comment_json
                )

                # print(RemoteCommentSerializer(unsaved_comment, context = {'request': self.request}).data)

                if response.ok:
                    print(response.content)
                    return HttpResponseRedirect(self.get_success_url())
                else:
                    return HttpResponseBadRequest(response.content)

        else:
            return self.form_invalid(form)

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
        form.instance.author_uuid = self.request.user.author.uuid
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('bettersocial:article_details', kwargs = { 'pk': self.kwargs['pk'] })


@method_decorator(login_required, name = 'dispatch')
class InboxView(generic.ListView):
    model = InboxItem
    template_name = 'bettersocial/inbox.html'
    context_object_name = 'inbox_items'

    def get_queryset(self):
        """Return all inbox items."""
        return InboxItem.objects.filter(author = self.request.user.author)


@method_decorator(login_required, name = 'dispatch')
class StreamView(generic.ListView):
    model = Post
    template_name = 'bettersocial/stream.html'
    context_object_name = 'stream_items'

    def get_context_data(self, *, object_list = None, **kwargs):
        context = super().get_context_data(object_list = object_list, **kwargs)

        data = list()

        queryset = InboxItem.objects.filter(author = self.request.user.author, inbox_object__iregex = '"type": "post"').all()

        for item in queryset:
            data.append(item.inbox_object)

        context[self.context_object_name] = data

        print(context[self.context_object_name])

        return context


@method_decorator(login_required, name = 'dispatch')
class PostLikesView(generic.ListView):
    model = Post
    template_name = 'bettersocial/list_of_likes.html'

    # TODO: not sure how this would work for remote servers
    # should we add username to model too?
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        post_uuid = self.kwargs['pk']
        post = Post.objects.get(pk = post_uuid)

        current_author = self.request.user.author
        post_author = post.author

        if post.author == current_author or current_author.friends_with(post_author.uuid):
            context['permitted'] = True
            context['likes'] = post.like_set.all()
            context['post'] = post
        else:
            context['permitted'] = False

        return context


@method_decorator(login_required, name = 'dispatch')
class FollowersView(generic.TemplateView):
    template_name = 'bettersocial/friends.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Different way to get author than normal. This is because we want to utilize the prefetch_related optimization. This ensures that the queries following_set.all() and follower_set.all() are preloaded.
        author: Author = Author.objects.filter(user_id = self.request.user.id).prefetch_related('following_set', 'follower_set').get()

        friends_list = author_helpers.get_author_friends(self.request, author)
        friend_request_list = list()

        # map the uuids of all the friends to here
        friends_list_uuid_pool = { uuid_helpers.extract_author_uuid_from_id(a['id']) for a in friends_list }

        for inbox_item in InboxItem.objects.filter(author = self.request.user.author, inbox_object__iregex = '"type": "follow"').all():

            # Do not include the request if the author is already a friend
            if uuid_helpers.extract_author_uuid_from_id(inbox_item.inbox_object['object']['id']) in friends_list_uuid_pool:
                print(f'{inbox_item.inbox_object["object"]["id"]} is already a friend, skipping...')
                continue

            friend_request_list.append(inbox_item.inbox_object)

        context['friend_request_list'] = [
            (follow_json['actor'], uuid_helpers.extract_author_uuid_from_id(follow_json['actor']['id'])) for follow_json in friend_request_list
        ]
        context['friends_list'] = [
            (author_json, uuid_helpers.extract_author_uuid_from_id(author_json['id'])) for author_json in friends_list
        ]

        return context


@method_decorator(login_required, name = 'dispatch')
class DeleteFollowingView(generic.DeleteView):

    def get_queryset(self):
        return Following.objects.none()

    def delete(self, request, *args, **kwargs):
        author_uuid = request.user.author.uuid
        following_uuid = request.POST.get('author_uuid')
        next_url = request.POST.get('next')

        # used as a backup in case next is not present
        success_url = reverse_lazy('bettersocial:friends')

        if not following_uuid:
            messages.add_message(request, messages.ERROR, 'author_uuid not present!')

        # Have to delete both relations (each row is from a different user perspective)
        Following.objects.filter(author_id = author_uuid, following_uuid = following_uuid).delete()
        Follower.objects.filter(author_id = following_uuid, follower_uuid = author_uuid).delete()

        messages.add_message(request, messages.INFO, 'Removed friend successfully.')

        return HttpResponseRedirect(next_url if next_url else success_url)


@method_decorator(login_required, name = 'dispatch')
class CreateFollowingView(generic.CreateView):

    def get_queryset(self):
        return Following.objects.none()

    def post(self, request, *args, **kwargs):

        author_uuid = request.user.author.uuid
        following_uuid = request.POST.get('author_uuid')
        next_url = request.POST.get('next')

        # used as a backup in case next is not present
        success_url = reverse_lazy('bettersocial:friends')

        if not following_uuid:
            messages.add_message(request, messages.ERROR, 'author_uuid not present!')

        # Author now follows following_uuid, and following_uuid is being followed by author (both need to be present)
        Following.objects.create(author_id = author_uuid, following_uuid = following_uuid)
        Follower.objects.create(author_id = following_uuid, follower_uuid = author_uuid)

        messages.add_message(request, messages.INFO, 'Friend added successfully.')

        return HttpResponseRedirect(next_url if next_url else success_url)


@method_decorator(login_required, name = 'dispatch')
class SharePostView(generic.DetailView):
    model = Post
    template_name = 'bettersocial/share_post.html'


@method_decorator(login_required, name = 'dispatch')
class SharePostActionView(generic.View):
    def post(self, request, uuid, action, *args, **kwargs):
        author = Author.objects.filter(uuid = request.user.author.uuid).get()
        original_post = Post.objects.get(pk = uuid)

        if action == 'everyone':
            visibility = "PUBLIC"
        elif action == 'friends':
            visibility = "FRIENDS"

        shared_post = Post(
            author = author,
            #    source = , NOT SURE WHAT TO PUT HERE or the link for origin
            origin = original_post.uuid,
            content_type = original_post.content_type,
            title = original_post.title,
            content = original_post.content,
            description = original_post.description,
            image_content = original_post.image_content,
            categories = original_post.categories,
            visibility = visibility,
        )

        shared_post.save()
        return HttpResponseRedirect(reverse('bettersocial:article_details', args = (shared_post.uuid,)))


@method_decorator(login_required, name = 'dispatch')
class EditProfileView(generic.UpdateView):
    template_name = 'bettersocial/edit_profile.html'
    form_class = EditProfileForm
    success_url = reverse_lazy('bettersocial:index')

    def get_object(self, **kwargs):
        return self.request.user


@method_decorator(login_required, name = 'dispatch')
class PasswordsChangeView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'bettersocial/change_password.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('bettersocial:index')
    success_message = "Password changed was successful"
