from django.urls import path

from .import views

urlpatterns = [
    path('dashboard/', views.profile_dashboard, name='dashboard'),
    path('profile-settings/', views.profile_settings, name='profile-settings'),
    path('my-ads/', views.profile_ads, name='profile-ads'),
    path('favorite-ads/', views.profile_favorite_ads, name='profile-favorite-ads'),
    path('favorite-ads/<int:pk>/remove/', views.profile_favorite_remove, name='favorite-remove'),
    path('profile-close/', views.profile_close, name='profile-close'),
]