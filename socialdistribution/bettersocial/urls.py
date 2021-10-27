from django.urls import path

from . import views

app_name = 'bettersocial'

urlpatterns = [
    path('', views.IndexView.as_view(), name = 'index'),
    path('post/', views.AddPostView.as_view(), name = 'post'),
    path('profile/', views.ProfileView.as_view(), name = 'profile'),
]
