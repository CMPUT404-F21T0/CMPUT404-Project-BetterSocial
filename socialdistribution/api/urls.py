from django.urls import path, include
from rest_framework_nested import routers

from . import views

app_name = 'api'

router = routers.DefaultRouter()
router.register(r'authors', views.AuthorViewSet)
router.register(r'author', views.AuthorViewSet)

author_router = routers.NestedSimpleRouter(router, r'author', lookup = 'author')
author_router.register(r'posts', views.PostViewSet)

post_router = routers.NestedSimpleRouter(author_router, r'posts', lookup = 'post')
post_router.register(r'comments', views.CommentViewSet)
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
