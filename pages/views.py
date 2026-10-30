from datetime import timedelta

from django.shortcuts import render, get_object_or_404
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Max, Prefetch, Q, Sum
from django.utils import timezone

from ads.models import Ads, State, City, Category, AdsImages, AdsTopBanner, AdsRightBanner, AdsBottomBanner, ListingReport

# Model Forms.

# Create your views here.

# Home view
def home(request):
    active_ads = Ads.objects.filter(
        is_active=True,
        status=Ads.Status.ACTIVE,
        is_flagged_hidden=False,
    )
    recent_ads = active_ads.select_related('author', 'category', 'state', 'city').prefetch_related(
        'adsimages_set'
    ).order_by('-date_created')[:8]
    featured_ads = active_ads.filter(is_featured=True).select_related(
        'author', 'category', 'state', 'city'
    ).prefetch_related('adsimages_set').order_by('-date_created')[:8]
    category_listing = (
        Category.objects.filter(parent__isnull=True, is_active=True)
        .prefetch_related(
            Prefetch(
                'subcategories',
                queryset=Category.objects.filter(is_active=True).order_by('display_order', 'category_name'),
            )
        )
        .annotate(
            total_ads=Count(
                'ads',
                filter=Q(
                    ads__is_active=True,
                    ads__status=Ads.Status.ACTIVE,
                    ads__is_flagged_hidden=False,
                ),
            )
        )
        .order_by('display_order', 'category_name')
    )
    live_cursor = active_ads.aggregate(cursor=Max('id'))['cursor'] or 0

    context = {
        'recent_ads': recent_ads,
        'featured_ads': featured_ads,
        'category_listing': category_listing,
        'live_cursor': live_cursor,
        'sidebar_banners': AdsRightBanner.objects.all(),
        'top_banner': AdsTopBanner.objects.all(),
        'bottom_banner': AdsBottomBanner.objects.all(),
        'state_search': State.objects.values_list('state_name', flat=True).distinct().order_by('state_name'),
        'category_search': Category.objects.values_list('category_name', flat=True).distinct().order_by('category_name'),
    }

    return render(request, 'pages/index.html', context)

# Faq view
def faq(request):
    return render(request, 'pages/faq.html')

# Terms of service view
def terms_of_service(request):
    return render(request, 'pages/terms-of-service.html')

# Contact view
def contact(request):
    return render(request, 'pages/contact.html')


@login_required(login_url='login')
@user_passes_test(lambda user: user.is_staff)
def marketplace_analytics(request):
    week_ago = timezone.now() - timedelta(days=7)
    active_ads = Ads.objects.filter(
        is_active=True,
        status=Ads.Status.ACTIVE,
        is_flagged_hidden=False,
    )
    context = {
        'active_listings': active_ads.count(),
        'total_listings': Ads.objects.count(),
        'estimated_value': active_ads.aggregate(total=Sum('price'))['total'] or 0,
        'new_users_this_week': get_user_model().objects.filter(date_joined__gte=week_ago).count(),
        'pending_reports': ListingReport.objects.filter(status=ListingReport.Status.PENDING).count(),
        'hidden_listings': Ads.objects.filter(is_flagged_hidden=True).count(),
    }
    return render(request, 'pages/marketplace-analytics.html', context)
