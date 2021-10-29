from django.urls import path

from . import views

app_name = 'bettersocial'

urlpatterns = [
    path('', views.IndexView.as_view(), name = 'index'),
    path('profile/<uuid:uuid>', views.ProfileView.as_view(), name = 'profile'),
    path('inbox/', views.InboxView.as_view(), name = 'inbox'),
    path('stream/', views.StreamView.as_view(), name = 'stream'),

    path('profile/<uuid:uuid>/<str:action>', views.ProfileActionView.as_view(), name = 'profile_action')
]
