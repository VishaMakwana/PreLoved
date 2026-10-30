from ads.models import Ads, Category, State
from django.db.models import Prefetch

def footer_recent_ads(request):
    ads = Ads.objects.filter(
        is_active=True,
        status=Ads.Status.ACTIVE,
        is_flagged_hidden=False,
    ).order_by('-date_created').prefetch_related('adsimages_set')[:2]
    return {
        'footer_recent_ads': ads,
        'nav_categories': Category.objects.filter(parent__isnull=True, is_active=True).prefetch_related(
            Prefetch(
                'subcategories',
                queryset=Category.objects.filter(is_active=True).order_by('display_order', 'category_name'),
            )
        ).order_by('display_order', 'category_name'),
        'all_categories': Category.objects.filter(is_active=True).order_by('display_order', 'category_name'),
        'nav_states': State.objects.all().order_by('state_name'),
    }
