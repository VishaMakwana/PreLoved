import logging
import json
import re
from smtplib import SMTPException
from decimal import Decimal, InvalidOperation

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseBadRequest, JsonResponse
from django.urls import reverse
from django.db import transaction
from django.db.models import Case, Count, F, IntegerField, Prefetch, Q, Value, When
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST
from PIL import Image, UnidentifiedImageError
from .models import (
    Ads,
    AdsImages,
    Author,
    Category,
    City,
    State,
    Wishlist,
    Offer,
    ChatMessage,
    ListingReport,
    UserAuditLog,
)
# Model Forms.
from .forms import AdsEditForm

from django.contrib.auth.decorators import login_required

from django.conf import settings
from django.core.mail import send_mail

# importing messages
from django.contrib import messages

logger = logging.getLogger(__name__)


def public_ads():
    return Ads.objects.filter(
        is_active=True,
        status=Ads.Status.ACTIVE,
        is_flagged_hidden=False,
    )


def _ad_image_url(ad):
    image = ad.adsimages_set.first()
    return image.image.url if image and image.image else ''


def _ad_feed_item(ad):
    return {
        'id': ad.pk,
        'title': ad.title,
        'price': str(ad.price),
        'condition': ad.condition,
        'city': str(ad.city or ''),
        'state': str(ad.state or ''),
        'category': str(ad.category or ''),
        'category_url': reverse('category-archive', kwargs={'slug': ad.category.slug}) if ad.category else '',
        'url': reverse('ads-detail', kwargs={'pk': ad.pk}),
        'image': _ad_image_url(ad),
    }


def _request_payload(request):
    if request.content_type == 'application/json':
        try:
            payload = json.loads(request.body or '{}')
        except json.JSONDecodeError:
            return None
        return payload if isinstance(payload, dict) else None
    return request.POST


def _image_upload_error(uploaded_images):
    for uploaded_image in uploaded_images:
        if uploaded_image.size > 15 * 1024 * 1024:
            return 'Each photo must be 15 MB or smaller.'
        try:
            with Image.open(uploaded_image) as image:
                image.verify()
                if image.width * image.height > 50_000_000:
                    return 'Photo dimensions must not exceed 50 megapixels.'
        except (OSError, UnidentifiedImageError):
            return 'Upload valid JPEG, PNG, or WebP photos.'
        finally:
            uploaded_image.seek(0)
    return ''
# Create your views here.

# Post ads view
@login_required(login_url='login')
def post_ads(request):
    if request.method == 'POST':
        # Part 1: Common Required Fields
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        category_val = request.POST.get('category', '').strip()
        price_val = request.POST.get('price', '').strip()
        condition = request.POST.get('condition', 'Good').strip()
        state_val = request.POST.get('state', '').strip()
        city_val = request.POST.get('city', '').strip()
        area = request.POST.get('area', '').strip()
        seller_name = request.POST.get('seller_name', '').strip()
        if not seller_name:
            seller_name = request.user.get_full_name() or request.user.username
        phone = request.POST.get('phone', '').strip()

        # Part 1: Common Optional Fields
        brand = request.POST.get('brand', '').strip()
        is_negotiable_val = request.POST.get('is_negotiable', 'false').lower()
        is_negotiable = is_negotiable_val in ['true', '1', 'yes', 'on']
        purchase_year = request.POST.get('purchase_year', '').strip()
        reason_for_selling = request.POST.get('reason_for_selling', '').strip()
        bill_or_warranty = request.POST.get('bill_or_warranty', '').strip()
        exchange_val = request.POST.get('exchange_accepted', 'false').lower()
        exchange_accepted = exchange_val in ['true', '1', 'yes', 'on']
        preferred_contact = request.POST.get('preferred_contact', 'Any').strip()
        delivery_available = request.POST.get('delivery_available', 'Pickup Only').strip()
        video = request.POST.get('video', '').strip()

        # Part 2: Category Extra Specifications
        extra_details_raw = request.POST.get('extra_details', '{}')
        try:
            extra_details = json.loads(extra_details_raw or '{}')
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Extra details must contain valid JSON.'}, status=400)
        if not isinstance(extra_details, dict):
            return JsonResponse({'status': 'error', 'message': 'Extra details must be a JSON object.'}, status=400)

        # Fallback for Brand if in extra_details
        if not brand:
            brand = extra_details.get('Brand') or extra_details.get('brand', '')

        # Photos validation: Minimum 2, Maximum 10 photos
        uploaded_images = []
        length_val = request.POST.get('length')
        if length_val and length_val.isdigit():
            for file_num in range(0, int(length_val)):
                img = request.FILES.get(f'images{file_num}')
                if img:
                    uploaded_images.append(img)
        if not uploaded_images and 'images' in request.FILES:
            uploaded_images = request.FILES.getlist('images')

        if len(uploaded_images) < 2:
            return JsonResponse({
                'status': 'error',
                'message': 'Please upload at least 2 photos (Minimum 2, Maximum 10 photos required).'
            }, status=400)

        if len(uploaded_images) > 10:
            return JsonResponse({
                'status': 'error',
                'message': 'Maximum 10 photos are allowed.'
            }, status=400)
        image_error = _image_upload_error(uploaded_images)
        if image_error:
            return JsonResponse({'status': 'error', 'message': image_error}, status=400)

        # Basic validations
        if not title:
            return JsonResponse({'status': 'error', 'message': 'Title cannot be empty.'}, status=400)
        if not description:
            return JsonResponse({'status': 'error', 'message': 'Description cannot be empty.'}, status=400)
        if not category_val:
            return JsonResponse({'status': 'error', 'message': 'Category must be selected.'}, status=400)
        if not price_val:
            return JsonResponse({'status': 'error', 'message': 'Price cannot be empty.'}, status=400)
        if not phone:
            return JsonResponse({'status': 'error', 'message': 'Phone number cannot be empty.'}, status=400)
        try:
            price = Decimal(price_val)
            if not price.is_finite() or price <= 0:
                raise InvalidOperation
        except (InvalidOperation, ValueError):
            return JsonResponse({'status': 'error', 'message': 'Enter a valid price greater than zero.'}, status=400)

        # Resolve category
        c = None
        if category_val:
            if category_val.isdigit():
                c = Category.objects.filter(id=int(category_val), is_active=True).first()
            if not c:
                c = Category.objects.filter(slug=category_val, is_active=True).first()
            if not c:
                c = Category.objects.filter(category_name=category_val, is_active=True).first()
        if not c:
            return JsonResponse({'status': 'error', 'message': 'Choose an available category.'}, status=400)

        # Resolve state and city
        s = None
        if state_val:
            s, _ = State.objects.get_or_create(state_name=state_val)

        ci = None
        if city_val:
            ci, _ = City.objects.get_or_create(city_name=city_val)

        author, _ = Author.objects.get_or_create(user=request.user)

        # Create Ad
        ads = Ads.objects.create(
            author=author,
            title=title,
            description=description,
            price=price,
            category=c,
            condition=condition,
            state=s,
            city=ci,
            area=area,
            seller_name=seller_name,
            brand=brand,
            phone=phone,
            is_phone_verified=False,
            video=video if video else None,
            is_negotiable=is_negotiable,
            purchase_year=purchase_year,
            reason_for_selling=reason_for_selling,
            bill_or_warranty=bill_or_warranty,
            exchange_accepted=exchange_accepted,
            preferred_contact=preferred_contact,
            delivery_available=delivery_available,
            extra_details=extra_details,
            is_active=True,
            status=Ads.Status.ACTIVE,
        )

        for img in uploaded_images:
            AdsImages.objects.create(ads=ads, image=img)

        notification_status = 'not_configured'
        if settings.EMAIL_HOST_USER and settings.EMAIL_HOST_PASSWORD and settings.EMAIL_HOST_PASSWORD != 'APP_PASSWORD':
            mail_subject = "New Ads submitted"
            sender_email = request.user.email
            message = f"Dear Admin, you received a new ads request from {sender_email} for '{title}'"
            to_email = settings.EMAIL_HOST_USER
            if to_email:
                try:
                    send_mail(mail_subject, message, settings.EMAIL_HOST_USER, [to_email], fail_silently=False)
                    notification_status = 'sent'
                except (SMTPException, OSError):
                    logger.exception('Listing %s was created but the admin notification could not be sent.', ads.pk)
                    notification_status = 'failed'

        return JsonResponse({
            'status': 'success',
            'message': 'Your Ad has been posted successfully!',
            'ad_id': ads.id,
            'redirect_url': reverse('ads-detail', kwargs={'pk': ads.id}),
            'notification_status': notification_status,
        })

    states = State.objects.all().order_by('state_name')
    categories = Category.objects.filter(parent__isnull=True, is_active=True).prefetch_related(
        Prefetch(
            'subcategories',
            queryset=Category.objects.filter(is_active=True).order_by('display_order', 'category_name'),
        )
    ).order_by('display_order', 'category_name')
    
    # Build category hierarchy JSON for dynamic UI
    cat_tree = []
    for cat in categories:
        subs = [
            {'id': sub.id, 'name': sub.category_name, 'slug': sub.slug}
            for sub in cat.subcategories.filter(is_active=True)
        ]
        cat_tree.append({
            'id': cat.id,
            'name': cat.category_name,
            'slug': cat.slug,
            'subcategories': subs
        })

    context = {
        'states': states,
        'categories': categories,
        'categories_json': json.dumps(cat_tree),
    }
    return render(request, 'ads/post-ads.html', context)

# Ads listing view
def ads_listing(request):
    ads_listing = public_ads().select_related('author', 'category', 'state', 'city').prefetch_related('adsimages_set')
    page_obj = Paginator(ads_listing.order_by('-date_created'), 16).get_page(request.GET.get('page'))
    category_listing = (
        Category.objects.filter(parent__isnull=True, is_active=True)
        .prefetch_related(
            Prefetch(
                'subcategories',
                queryset=Category.objects.filter(is_active=True).order_by('display_order', 'category_name'),
            )
        )
        .annotate(total_ads=Count('ads', filter=Q(ads__is_active=True, ads__status=Ads.Status.ACTIVE, ads__is_flagged_hidden=False)))
        .order_by('category_name')
    )

    context = {
        'ads_listing': page_obj.object_list,
        'page_obj': page_obj,
        'category_listing': category_listing,
    }

    return render(request, 'ads/ads-listing.html', context)

# Ads detail view
def ads_detail(request, pk):
    ads_detail = get_object_or_404(Ads, pk=pk)
    if ads_detail.is_flagged_hidden or not ads_detail.is_active:
        if not request.user.is_authenticated or (
            request.user != getattr(ads_detail.author, 'user', None) and not request.user.is_staff
        ):
            from django.http import Http404
            raise Http404
    Ads.objects.filter(pk=ads_detail.pk).update(view_count=F('view_count') + 1)
    ads_detail.refresh_from_db(fields=['view_count', 'status'])
    ads_photos = AdsImages.objects.filter(ads=ads_detail)
    is_owner = request.user.is_authenticated and ads_detail.author and ads_detail.author.user_id == request.user.pk
    can_chat = request.user.is_authenticated and (
        is_owner
        or ads_detail.chat_messages.filter(sender=request.user).exists()
        or ads_detail.offers.filter(buyer=request.user).exists()
    )

    chat_messages = list(ads_detail.chat_messages.select_related('sender').all()[:50]) if can_chat else []
    context = {
        'ads_detail': ads_detail,
        'ads_photos': ads_photos,
        'is_favorite': request.user.is_authenticated and Wishlist.objects.filter(user=request.user, ad=ads_detail).exists(),
        'favorite_count': ads_detail.wishlist_items.count(),
        'offers': ads_detail.offers.select_related('buyer').all() if request.user.is_authenticated and (
            is_owner or ads_detail.offers.filter(buyer=request.user).exists()
        ) else [],
        'chat_messages': chat_messages,
        'chat_cursor': chat_messages[-1].pk if chat_messages else 0,
        'can_manage_ad': is_owner,
        'can_chat': can_chat,
    }

    return render(request, 'ads/ads-detail.html', context)

# Ads category archive view
def ads_category_archive(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    subcategories = category.subcategories.filter(is_active=True)
    if subcategories.exists():
        ads_by_category = public_ads().filter(Q(category=category) | Q(category__in=subcategories)).distinct()
    else:
        ads_by_category = public_ads().filter(category=category)

    context = {
        'category' : category,
        'ads_by_category' : ads_by_category,
        'subcategories': subcategories
    }

    return render(request, 'ads/category-archive.html', context)

# Ads state archive view
def ads_state_archive(request, slug):
    state = get_object_or_404(State, slug=slug)
    ads_by_state = public_ads().filter(state=state)

    context = {
        'state' : state,
        'ads_by_state' : ads_by_state
    }

    return render(request, 'ads/state-archive.html', context)

# Ads city archive view
def ads_city_archive(request, slug):
    city = get_object_or_404(City, slug=slug)
    ads_by_city = public_ads().filter(city=city)

    context = {
        'city' : city,
        'ads_by_city' : ads_by_city
    }

    return render(request, 'ads/city-archive.html', context)

# Ads author archive view
def ads_author_archive(request, pk):
    author = get_object_or_404(Author, pk=pk)
    ads_by_author = public_ads().filter(author=author)

    context = {
        'author' : author,
        'ads_by_author' : ads_by_author
    }

    return render(request, 'ads/author-archive.html', context)

# Ads search/filter view
def ads_search(request):

    state = request.GET.get('state_name', '')
    category = request.GET.get('category_name', '')
    customword = request.GET.get('customword', '').strip()
    city = request.GET.get('city', '').strip()
    condition = request.GET.get('condition', '')
    sort = request.GET.get('sort', 'newest')
    min_price = request.GET.get('min_price', '').strip()
    max_price = request.GET.get('max_price', '').strip()
    ads_search_result = public_ads().select_related('author', 'category', 'state', 'city').prefetch_related('adsimages_set')
    if state and state != 'Select State':
        ads_search_result = ads_search_result.filter(state__state_name=state)
    if category and category != 'Select Category' and category != '':
        cat_obj = Category.objects.filter(category_name=category, is_active=True).first()
        active_subcategories = cat_obj.subcategories.filter(is_active=True) if cat_obj else Category.objects.none()
        if active_subcategories.exists():
            ads_search_result = ads_search_result.filter(
                Q(category=cat_obj) | Q(category__in=active_subcategories)
            )
        else:
            ads_search_result = ads_search_result.filter(category__category_name=category)
    if customword:
        tokens = [token for token in re.findall(r'[\w-]+', customword) if token.lower() not in {
            'a', 'an', 'and', 'for', 'in', 'of', 'or', 'the', 'to', 'with',
        }]
        if not tokens:
            tokens = [customword]
        search_query = Q()
        relevance = Value(0, output_field=IntegerField())
        for token in tokens:
            search_query |= Q(title__icontains=token) | Q(description__icontains=token) | Q(brand__icontains=token)
            relevance += Case(
                When(title__icontains=token, then=Value(3)),
                default=Value(0),
                output_field=IntegerField(),
            )
            relevance += Case(
                When(description__icontains=token, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            )
        ads_search_result = ads_search_result.filter(search_query).annotate(relevance=relevance)
    if city:
        ads_search_result = ads_search_result.filter(city__city_name__icontains=city)
    if condition:
        ads_search_result = ads_search_result.filter(condition=condition)
    price_bounds = {}
    for parameter, raw_value, field, label in (
        ('min_price', min_price, 'price__gte', 'Minimum price'),
        ('max_price', max_price, 'price__lte', 'Maximum price'),
    ):
        if raw_value:
            try:
                amount = Decimal(raw_value)
                if not amount.is_finite() or amount < 0:
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                messages.error(request, f'{label} must be a non-negative number.')
                continue
            price_bounds[parameter] = amount
            ads_search_result = ads_search_result.filter(**{field: amount})
    if price_bounds.get('min_price') is not None and price_bounds.get('max_price') is not None:
        if price_bounds['min_price'] > price_bounds['max_price']:
            messages.error(request, 'Minimum price cannot exceed maximum price.')
    if sort == 'price_asc':
        ads_search_result = ads_search_result.order_by('price', '-date_created')
    elif sort == 'price_desc':
        ads_search_result = ads_search_result.order_by('-price', '-date_created')
    elif customword:
        ads_search_result = ads_search_result.order_by('-relevance', '-date_created')
    else:
        ads_search_result = ads_search_result.order_by('-date_created')
    page_obj = Paginator(ads_search_result, 16).get_page(request.GET.get('page'))
    context = {
        'ads_search_result': page_obj.object_list,
        'page_obj': page_obj,
        'state_name': state,
        'category_name': category,
        'customword': customword,
        'city': city,
        'condition': condition,
        'sort': sort,
        'min_price': min_price,
        'max_price': max_price,
        'states': State.objects.order_by('state_name'),
        'categories': Category.objects.filter(is_active=True).order_by('display_order', 'category_name'),
        'conditions': Ads.CONDITION,
    }

    return render(request, 'ads/ads-search.html', context)

# Ads delete view
@login_required(login_url='login')
@require_POST
def ads_delete(request, pk):
    ad = get_object_or_404(Ads, pk=pk, author__user=request.user)
    ad.status = Ads.Status.ARCHIVED
    ad.is_active = False
    ad.save(update_fields=['status', 'is_active'])
    messages.success(request, 'Your listing has been archived.')
    return redirect('profile-ads')


@login_required(login_url='login')
def ads_edit(request, pk):
    ad = get_object_or_404(Ads, pk=pk, author__user=request.user)
    original_phone = ad.phone
    if request.method == 'POST':
        form = AdsEditForm(request.POST, instance=ad)
        new_images = request.FILES.getlist('images')
        image_error = _image_upload_error(new_images)
        if len(new_images) + ad.adsimages_set.count() > 10:
            image_error = 'A listing can have no more than 10 photos.'
        elif len(new_images) + ad.adsimages_set.count() < 2:
            image_error = 'A listing must have at least 2 photos.'
        if image_error:
            messages.error(request, image_error)
        elif form.is_valid():
            with transaction.atomic():
                updated_ad = form.save(commit=False)
                if form.cleaned_data['phone'] != original_phone:
                    updated_ad.is_phone_verified = False
                updated_ad.save()
                for image in new_images:
                    AdsImages.objects.create(ads=updated_ad, image=image)
            messages.success(request, 'Your listing has been updated.')
            return redirect('ads-detail', pk=ad.pk)
    else:
        form = AdsEditForm(instance=ad)
    return render(request, 'ads/edit-ads.html', {
        'form': form,
        'ad': ad,
        'ad_images': ad.adsimages_set.all(),
    })


@require_POST
@login_required(login_url='login')
def update_listing_status(request, pk):
    ad = get_object_or_404(Ads, pk=pk, author__user=request.user)
    previous_status = ad.status
    requested_status = request.POST.get('status', '')
    allowed_statuses = {
        Ads.Status.ACTIVE,
        Ads.Status.DEAL_PENDING,
        Ads.Status.SOLD,
        Ads.Status.ARCHIVED,
    }
    if requested_status not in allowed_statuses:
        return HttpResponseBadRequest('Unsupported listing status.')
    if requested_status == Ads.Status.ACTIVE and ad.is_flagged_hidden:
        return HttpResponseBadRequest('A reported listing must be reviewed by staff before republishing.')
    ad.status = requested_status
    ad.is_active = requested_status != Ads.Status.ARCHIVED
    ad.save(update_fields=['status', 'is_active'])
    UserAuditLog.objects.create(
        actor=request.user,
        subject=request.user,
        ad=ad,
        action='LISTING_STATUS_CHANGED',
        details={'from': previous_status, 'to': requested_status},
    )
    if requested_status in {Ads.Status.SOLD, Ads.Status.ARCHIVED}:
        ad.offers.filter(status__in=[Offer.Status.PENDING, Offer.Status.COUNTERED]).update(status=Offer.Status.EXPIRED)
    messages.success(request, f'Listing marked {ad.get_status_display().lower()}.')
    return redirect('profile-ads')


@require_GET
def api_live_feed(request):
    try:
        after_id = max(int(request.GET.get('after_id', '0')), 0)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'after_id must be a non-negative integer.'}, status=400)

    listings = public_ads().filter(pk__gt=after_id).select_related(
        'category', 'city', 'state'
    ).prefetch_related('adsimages_set')
    category_id = request.GET.get('category')
    if category_id:
        try:
            category = Category.objects.get(pk=int(category_id), is_active=True)
        except (ValueError, Category.DoesNotExist):
            return JsonResponse({'error': 'category must identify an existing category.'}, status=400)
        descendants = category.subcategories.values_list('pk', flat=True)
        listings = listings.filter(Q(category=category) | Q(category__in=descendants))
    city = request.GET.get('city', '').strip()
    if city:
        listings = listings.filter(city__city_name__iexact=city)

    batch = list(listings.order_by('pk')[:20])
    return JsonResponse({
        'items': [_ad_feed_item(ad) for ad in batch],
        'cursor': max([after_id, *(ad.pk for ad in batch)]),
    })


@require_GET
def api_listings(request):
    listings = public_ads().select_related('category', 'city', 'state').prefetch_related('adsimages_set')
    query = request.GET.get('q', '').strip()
    city = request.GET.get('city', '').strip()
    category_id = request.GET.get('category', '').strip()
    condition = request.GET.get('condition', '').strip()
    sort = request.GET.get('sort', 'newest')

    if query:
        listings = listings.filter(Q(title__icontains=query) | Q(description__icontains=query) | Q(brand__icontains=query))
    if city:
        listings = listings.filter(city__city_name__icontains=city)
    if condition:
        listings = listings.filter(condition=condition)
    if category_id:
        try:
            category = Category.objects.get(pk=int(category_id), is_active=True)
        except (ValueError, Category.DoesNotExist):
            return JsonResponse({'error': 'category must identify an existing category.'}, status=400)
        listings = listings.filter(Q(category=category) | Q(category__in=category.subcategories.all()))
    price_values = {}
    for parameter, lookup in (('min_price', 'price__gte'), ('max_price', 'price__lte')):
        raw_value = request.GET.get(parameter, '').strip()
        if raw_value:
            try:
                amount = Decimal(raw_value)
                if not amount.is_finite() or amount < 0:
                    raise InvalidOperation
            except (InvalidOperation, ValueError):
                return JsonResponse({'error': f'{parameter} must be a non-negative number.'}, status=400)
            price_values[parameter] = amount
            listings = listings.filter(**{lookup: amount})
    if price_values.get('min_price') is not None and price_values.get('max_price') is not None:
        if price_values['min_price'] > price_values['max_price']:
            return JsonResponse({'error': 'min_price cannot exceed max_price.'}, status=400)
    if sort == 'price_asc':
        listings = listings.order_by('price', '-date_created')
    elif sort == 'price_desc':
        listings = listings.order_by('-price', '-date_created')
    else:
        listings = listings.order_by('-date_created')

    page_obj = Paginator(listings, 16).get_page(request.GET.get('page'))
    return JsonResponse({
        'results': [_ad_feed_item(ad) for ad in page_obj.object_list],
        'page': page_obj.number,
        'pages': page_obj.paginator.num_pages,
        'total': page_obj.paginator.count,
    })


@require_POST
@login_required(login_url='login')
def wishlist_toggle(request, pk):
    ad = get_object_or_404(public_ads(), pk=pk)
    if ad.author and ad.author.user_id == request.user.pk:
        return JsonResponse({'error': 'You cannot save your own listing.'}, status=400)
    saved, created = Wishlist.objects.get_or_create(user=request.user, ad=ad)
    if not created:
        saved.delete()
        is_saved = False
    else:
        is_saved = True
    return JsonResponse({
        'saved': is_saved,
        'count': ad.wishlist_items.count(),
    })


@require_POST
@login_required(login_url='login')
def create_offer(request, pk):
    payload = _request_payload(request)
    if payload is None:
        return JsonResponse({'error': 'Request body must be valid JSON.'}, status=400)
    try:
        amount = Decimal(str(payload.get('amount', '')))
        if not amount.is_finite():
            raise InvalidOperation
    except (InvalidOperation, ValueError):
        return JsonResponse({'error': 'Enter a valid offer amount.'}, status=400)

    with transaction.atomic():
        ad = get_object_or_404(public_ads().select_for_update(), pk=pk)
        if ad.author and ad.author.user_id == request.user.pk:
            return JsonResponse({'error': 'You cannot make an offer on your own listing.'}, status=400)
        if amount < ad.price * Decimal('0.10') or amount > ad.price * Decimal('1.50'):
            return JsonResponse({'error': 'Offer must be between 10% and 150% of the asking price.'}, status=400)
        offer = Offer.objects.create(ad=ad, buyer=request.user, amount=amount)
    return JsonResponse({'id': offer.pk, 'status': offer.status, 'amount': str(offer.amount)}, status=201)


@require_POST
@login_required(login_url='login')
def respond_to_offer(request, pk):
    payload = _request_payload(request)
    if payload is None:
        return JsonResponse({'error': 'Request body must be valid JSON.'}, status=400)
    decision = str(payload.get('decision', '')).upper()

    with transaction.atomic():
        offer = get_object_or_404(
            Offer.objects.select_for_update().select_related('ad', 'ad__author'),
            pk=pk,
        )
        ad = Ads.objects.select_for_update().get(pk=offer.ad_id)
        is_seller = ad.author and ad.author.user_id == request.user.pk
        if is_seller:
            if offer.status != Offer.Status.PENDING or ad.status != Ads.Status.ACTIVE:
                return JsonResponse({'error': 'This offer is no longer pending.'}, status=409)
            if decision == 'COUNTER':
                try:
                    counter_amount = Decimal(str(payload.get('amount', '')))
                    if not counter_amount.is_finite():
                        raise InvalidOperation
                except (InvalidOperation, ValueError):
                    return JsonResponse({'error': 'Enter a valid counter-offer amount.'}, status=400)
                if counter_amount < ad.price * Decimal('0.10') or counter_amount > ad.price * Decimal('1.50'):
                    return JsonResponse({'error': 'Counter-offer must be between 10% and 150% of the asking price.'}, status=400)
                offer.counter_amount = counter_amount
                offer.status = Offer.Status.COUNTERED
                offer.save(update_fields=['counter_amount', 'status', 'updated_at'])
            elif decision == 'REJECT':
                offer.status = Offer.Status.REJECTED
                offer.save(update_fields=['status', 'updated_at'])
            elif decision == 'ACCEPT':
                offer.status = Offer.Status.ACCEPTED
                offer.save(update_fields=['status', 'updated_at'])
                ad.status = Ads.Status.DEAL_PENDING
                ad.save(update_fields=['status'])
                ad.offers.exclude(pk=offer.pk).filter(
                    status__in=[Offer.Status.PENDING, Offer.Status.COUNTERED]
                ).update(status=Offer.Status.EXPIRED)
            else:
                return JsonResponse({'error': 'Decision must be ACCEPT, REJECT, or COUNTER.'}, status=400)
        elif offer.buyer_id == request.user.pk:
            if offer.status != Offer.Status.COUNTERED:
                return JsonResponse({'error': 'Only a countered offer can be answered by its buyer.'}, status=409)
            if decision == 'ACCEPT' and ad.status == Ads.Status.ACTIVE:
                offer.status = Offer.Status.ACCEPTED
                ad.status = Ads.Status.DEAL_PENDING
                ad.save(update_fields=['status'])
                ad.offers.exclude(pk=offer.pk).filter(
                    status__in=[Offer.Status.PENDING, Offer.Status.COUNTERED]
                ).update(status=Offer.Status.EXPIRED)
            elif decision == 'REJECT':
                offer.status = Offer.Status.REJECTED
            else:
                return JsonResponse({'error': 'Decision must be ACCEPT or REJECT.'}, status=400)
            offer.save(update_fields=['status', 'updated_at'])
        else:
            return JsonResponse({'error': 'You are not a participant in this offer.'}, status=403)

    return JsonResponse({
        'id': offer.pk,
        'status': offer.status,
        'counter_amount': str(offer.counter_amount) if offer.counter_amount is not None else None,
    })


@require_POST
@login_required(login_url='login')
def cancel_offer(request, pk):
    with transaction.atomic():
        offer = get_object_or_404(Offer.objects.select_for_update(), pk=pk, buyer=request.user)
        if offer.status not in {Offer.Status.PENDING, Offer.Status.COUNTERED}:
            return JsonResponse({'error': 'Only pending offers can be cancelled.'}, status=409)
        offer.status = Offer.Status.CANCELLED
        offer.save(update_fields=['status', 'updated_at'])
    return JsonResponse({'id': offer.pk, 'status': offer.status})


def _can_read_chat(ad, user):
    return (
        (ad.author and ad.author.user_id == user.pk)
        or ChatMessage.objects.filter(ad=ad, sender=user).exists()
        or Offer.objects.filter(ad=ad, buyer=user).exists()
    )


@require_GET
def chat_messages(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Sign in to view this conversation.'}, status=401)
    ad = get_object_or_404(Ads, pk=pk)
    if not _can_read_chat(ad, request.user):
        return JsonResponse({'error': 'You are not a participant in this conversation.'}, status=403)
    try:
        after_id = max(int(request.GET.get('after_id', '0')), 0)
    except (TypeError, ValueError):
        return JsonResponse({'error': 'after_id must be a non-negative integer.'}, status=400)
    ChatMessage.objects.filter(ad=ad, read_at__isnull=True).exclude(sender=request.user).update(read_at=timezone.now())
    messages_qs = ad.chat_messages.select_related('sender').order_by('created_at')
    if after_id:
        messages_qs = messages_qs.filter(pk__gt=after_id)
    return JsonResponse({
        'messages': [{
            'id': message.pk,
            'sender': message.sender.get_username(),
            'body': message.body,
            'created_at': message.created_at.isoformat(),
            'read': message.read_at is not None,
        } for message in messages_qs[:100]],
    })


@require_POST
@login_required(login_url='login')
def send_chat_message(request, pk):
    payload = _request_payload(request)
    if payload is None:
        return JsonResponse({'error': 'Request body must be valid JSON.'}, status=400)
    body = str(payload.get('body', '')).strip()
    if not body or len(body) > 4000:
        return JsonResponse({'error': 'Message must contain 1 to 4000 characters.'}, status=400)
    ad = get_object_or_404(Ads, pk=pk)
    is_seller = ad.author and ad.author.user_id == request.user.pk
    if not is_seller and (not ad.is_active or ad.status not in {Ads.Status.ACTIVE, Ads.Status.DEAL_PENDING} or ad.is_flagged_hidden):
        return JsonResponse({'error': 'This listing is not accepting messages.'}, status=409)
    message = ChatMessage.objects.create(ad=ad, sender=request.user, body=body)
    return JsonResponse({
        'id': message.pk,
        'sender': message.sender.get_username(),
        'body': message.body,
        'created_at': message.created_at.isoformat(),
        'read': False,
    }, status=201)


@require_POST
@login_required(login_url='login')
def report_listing(request, pk):
    payload = _request_payload(request)
    if payload is None:
        return JsonResponse({'error': 'Request body must be valid JSON.'}, status=400)
    reason = str(payload.get('reason', '')).upper()
    if reason not in ListingReport.Reason.values:
        return JsonResponse({'error': 'Choose a valid report reason.'}, status=400)
    details = str(payload.get('details', '')).strip()
    if len(details) > 2000:
        return JsonResponse({'error': 'Report details cannot exceed 2000 characters.'}, status=400)
    with transaction.atomic():
        ad = get_object_or_404(public_ads().select_for_update(), pk=pk)
        if ad.author and ad.author.user_id == request.user.pk:
            return JsonResponse({'error': 'You cannot report your own listing.'}, status=400)
        report, created = ListingReport.objects.get_or_create(
            ad=ad,
            reporter=request.user,
            defaults={'reason': reason, 'details': details},
        )
        if not created:
            return JsonResponse({'error': 'You have already reported this listing.'}, status=409)
        report_count = ad.reports.filter(status=ListingReport.Status.PENDING).count()
        if report_count >= 3:
            ad.is_flagged_hidden = True
            ad.save(update_fields=['is_flagged_hidden'])
    return JsonResponse({
        'status': report.status,
        'pending_reports': report_count,
        'hidden_pending_review': ad.is_flagged_hidden,
    }, status=201)


@require_POST
@login_required(login_url='login')
def moderate_listing(request):
    if not request.user.is_staff:
        return JsonResponse({'error': 'Staff access is required.'}, status=403)
    payload = _request_payload(request)
    if payload is None:
        return JsonResponse({'error': 'Request body must be valid JSON.'}, status=400)
    try:
        ad_id = int(payload.get('listing_id'))
    except (TypeError, ValueError):
        return JsonResponse({'error': 'listing_id must be an integer.'}, status=400)
    action = str(payload.get('action', '')).lower()
    with transaction.atomic():
        ad = get_object_or_404(Ads.objects.select_for_update().select_related('author'), pk=ad_id)
        if action == 'approve':
            ad.is_flagged_hidden = False
            ad.is_active = True
            ad.status = Ads.Status.ACTIVE
            ad.save(update_fields=['is_flagged_hidden', 'is_active', 'status'])
            ad.reports.filter(status=ListingReport.Status.PENDING).update(status=ListingReport.Status.RESOLVED)
        elif action == 'remove':
            ad.is_flagged_hidden = True
            ad.is_active = False
            ad.status = Ads.Status.ARCHIVED
            ad.save(update_fields=['is_flagged_hidden', 'is_active', 'status'])
            ad.reports.filter(status=ListingReport.Status.PENDING).update(status=ListingReport.Status.RESOLVED)
        elif action == 'ban':
            if not ad.author:
                return JsonResponse({'error': 'This listing has no seller account to suspend.'}, status=400)
            ad.author.user.is_active = False
            ad.author.user.save(update_fields=['is_active'])
            Ads.objects.filter(author=ad.author).update(
                is_flagged_hidden=True,
                is_active=False,
                status=Ads.Status.ARCHIVED,
            )
            ad.refresh_from_db(fields=['status', 'is_active', 'is_flagged_hidden'])
        else:
            return JsonResponse({'error': 'Action must be approve, remove, or ban.'}, status=400)
        UserAuditLog.objects.create(
            actor=request.user,
            subject=ad.author.user if ad.author else None,
            ad=ad,
            action=f'LISTING_{action.upper()}',
            details={'listing_id': ad.pk},
        )
    return JsonResponse({'listing_id': ad.pk, 'action': action, 'status': ad.status})
