from django.urls import path, include
from rest_framework_nested import routers

from . import views

app_name = 'api'

router = routers.DefaultRouter(trailing_slash = '/?')
router.register(r'authors?', views.AuthorViewSet)

# Local helper api calls
router.register(r'posts', views.AllPostsViewSet, basename = 'local-post')
router.register(r'remote-posts', views.AllRemotePostsViewSet, basename = 'remote-post')
router.register(r'send-post', views.SendPostRemoteViewSet, basename = 'send-post')

author_router = routers.NestedSimpleRouter(router, r'authors?', lookup = 'author')
author_router.register(r'posts', views.PostViewSet, basename = 'post')
author_router.register(r'inbox', views.InboxItemViewSet, basename = 'inbox')
author_router.register(r'followers', views.FollowerViewSet, basename = 'follower')

post_router = routers.NestedSimpleRouter(author_router, r'posts', lookup = 'post')
post_router.register(r'comments', views.CommentViewSet, basename = 'comment')
post_router.register(r'likes', views.PostLikeViewSet, basename = 'post-like')

comment_router = routers.NestedSimpleRouter(post_router, r'comments', lookup = 'comment')
comment_router.register(r'likes', views.CommentLikeViewSet, basename = 'comment-like')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(author_router.urls)),
    path('', include(post_router.urls)),
    path('', include(comment_router.urls)),
    path('api-auth/', include('rest_framework.urls'), name = 'rest_framework'),
]
