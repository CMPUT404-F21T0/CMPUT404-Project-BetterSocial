from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, register_converter

from . import views, converters

register_converter(converters.BetterUUIDConverter, 'buuid')

app_name = 'bettersocial'

urlpatterns = [
    path('', views.StreamView.as_view(), name = 'index'),
    path('post/', views.AddPostView.as_view(), name = 'post'),
    path('article/<buuid:pk>/', views.ArticleDetailView.as_view(), name = 'article_details'),
    path('article/<buuid:pk>/comment/', views.AddCommentView.as_view(), name = 'add_comment'),
    path('article/<buuid:pk>/likes/', views.PostLikesView.as_view(), name = 'post_likes_list'),
    path('article/<buuid:pk>/remove/', views.DeletePostView.as_view(), name = 'delete_post'),
    path('article/edit/<buuid:pk>/', views.UpdatePostView.as_view(), name = 'edit_post'),
    path('profile/<buuid:uuid>', views.ProfileView.as_view(), name = 'profile'),
    path('profile/<buuid:uuid>/<str:action>', views.ProfileActionView.as_view(), name = 'profile_action'),
    path('inbox/', views.InboxView.as_view(), name = 'inbox'),
    path('friends/', views.FollowersView.as_view(), name = 'friends'),
    path('delete-following/', views.DeleteFollowingView.as_view(), name = 'delete_following'),
    path('add-following/', views.CreateFollowingView.as_view(), name = 'add_following'),
    path('article/<buuid:pk>/share/', views.SharePostView.as_view(), name = 'share_post'),
    path('article/<buuid:uuid>/share/<str:action>', views.SharePostActionView.as_view(), name = 'share_post_action'),
]

urlpatterns += static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
