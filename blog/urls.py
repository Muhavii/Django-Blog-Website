from django.urls import path
from . import views
from django.views.generic import RedirectView

urlpatterns = [
    path('', views.home, name='home'),
    path('post/<int:pk>/', views.post_detail, name='post_detail'),
    path('post/new/', views.create_post, name='create_post'),
    path('post/<int:pk>/edit/', views.edit_post, name='edit_post'),
    path('post/<int:pk>/delete/', views.delete_post, name='delete_post'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('like/<int:post_id>/', views.like_post, name='like_post'),
    path('profile/settings/', views.profile_settings, name='profile_settings'),
    path('profile/<str:username>/', views.profile_view, name='profile_view'),
    path('profile/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('profile/<str:username>/followers/', views.followers_list, name='followers_list'),
    path('profile/<str:username>/following/', views.following_list, name='following_list'),
    path('profile/<str:username>/followers/modal/', views.followers_modal, name='followers_modal'),
    path('profile/<str:username>/following/modal/', views.following_modal, name='following_modal'),
    path('search/', views.user_search, name='user_search'),
    path('users/', RedirectView.as_view(pattern_name='user_search', permanent=False)),
]
