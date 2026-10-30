from django.urls import path

from .import views

urlpatterns = [
    path('post-ads/', views.post_ads, name='post-ads'),
    path('ads-listing/', views.ads_listing, name='ads-listing'),
    path('api/v1/listings/', views.api_listings, name='api-listings'),
    path('api/v1/listings/create/', views.post_ads, name='api-listing-create'),
    path('api/v1/feed/live/', views.api_live_feed, name='api-live-feed'),
    path('api/v1/listings/<int:pk>/wishlist/', views.wishlist_toggle, name='api-wishlist-toggle'),
    path('api/v1/listings/<int:pk>/offers/', views.create_offer, name='api-offer-create'),
    path('api/v1/offers/<int:pk>/respond/', views.respond_to_offer, name='api-offer-respond'),
    path('api/v1/offers/<int:pk>/cancel/', views.cancel_offer, name='api-offer-cancel'),
    path('api/v1/chat/<int:pk>/', views.chat_messages, name='api-chat-messages'),
    path('api/v1/chat/<int:pk>/send/', views.send_chat_message, name='api-chat-send'),
    path('api/v1/listings/<int:pk>/report/', views.report_listing, name='api-listing-report'),
    path('api/v1/admin/moderate/', views.moderate_listing, name='api-listing-moderate'),
    path('ads/<int:pk>/edit/', views.ads_edit, name='ads-edit'),
    path('ads/<int:pk>/status/', views.update_listing_status, name='ads-status-update'),
    path('ads/<int:pk>/', views.ads_detail, name='ads-detail'),
    path('ads/<int:pk>/delete/', views.ads_delete, name='ads-delete'),
    path('category/<slug:slug>/', views.ads_category_archive, name='category-archive'),
    path('state/<slug:slug>/', views.ads_state_archive, name='state-archive'),
    path('city/<slug:slug>/', views.ads_city_archive, name='city-archive'),
    path('author/<int:pk>/', views.ads_author_archive, name='author-archive'),
    path('ads-search/', views.ads_search, name='ads-search'),
]