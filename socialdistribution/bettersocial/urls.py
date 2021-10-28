from django.conf.urls import url
from django.urls import path

from . import views

app_name = 'bettersocial'

urlpatterns = [
    path('', views.IndexView.as_view(), name = 'index'),
    path('post/', views.AddPostView.as_view(), name = 'post'),
    # (?P<pk>[\w-]+) --> in url() is used as a PK for the post
    url(r'^article/(?P<pk>[\w-]+)/$', views.ArticleDetailView.as_view(), name='article_details'),
    url(r'^article/edit/(?P<pk>[\w-]+)/$', views.UpdatePostView.as_view(), name='edit_post'),
    url(r'^article/(?P<pk>[\w-]+)/remove/$', views.DeletePostView.as_view(), name='delete_post'),
    url(r'^article/(?P<pk>[\w-]+)/comment/$', views.AddCommentView.as_view(), name='add_comment'),
    path('profile/', views.ProfileView.as_view(), name = 'profile'),
]
