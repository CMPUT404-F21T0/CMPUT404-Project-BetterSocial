from django.conf.urls import url
from django.urls import path

from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'bettersocial'

urlpatterns = [
    path('', views.IndexView.as_view(), name = 'index'),
    path('post/', views.AddPostView.as_view(), name = 'post'),
    path('article/<uuid:pk>/', views.ArticleDetailView.as_view(), name='article_details'),
    path('article/edit/<uuid:pk>/', views.UpdatePostView.as_view(), name='edit_post'),
    path('article/<uuid:pk>/remove/', views.DeletePostView.as_view(), name='delete_post'),
    path('article/<uuid:pk>/comment/', views.AddCommentView.as_view(), name='add_comment'),
    path('profile/<uuid:uuid>', views.ProfileView.as_view(), name = 'profile'),
    path('inbox/', views.InboxView.as_view(), name = 'inbox'),
    path('stream/', views.StreamView.as_view(), name = 'stream'),

]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
