from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

app_name = 'bettersocial'

urlpatterns = [
    path('', views.StreamView.as_view(), name = 'index'),
    path('post/', views.AddPostView.as_view(), name = 'post'),
    path('article/<uuid:pk>/', views.ArticleDetailView.as_view(), name = 'article_details'),
    path('article/<uuid:pk>/comment/', views.AddCommentView.as_view(), name = 'add_comment'),
    path('article/<uuid:pk>/likes/', views.PostLikesView.as_view(), name = 'post_likes_list'),
    path('article/<uuid:pk>/remove/', views.DeletePostView.as_view(), name = 'delete_post'),
    path('article/edit/<uuid:pk>/', views.UpdatePostView.as_view(), name = 'edit_post'),
    path('profile/<uuid:uuid>', views.ProfileView.as_view(), name = 'profile'),
    path('inbox/', views.InboxView.as_view(), name = 'inbox'),
    path('friends/', views.FollowersView.as_view(), name = 'friends'),
    path('delete-following/', views.DeleteFollowingView.as_view(), name = 'delete_following'),
    path('add-following/', views.CreateFollowingView.as_view(), name = 'add_following'),
]

urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
