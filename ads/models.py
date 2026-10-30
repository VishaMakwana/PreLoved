import uuid
from io import BytesIO

from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from ckeditor.fields import RichTextField
from django.utils.text import slugify
from django.urls import reverse
# Default User model
from django.contrib.auth.models import User

from embed_video.fields import EmbedVideoField
from PIL import Image, ImageOps, UnidentifiedImageError

# Create your models here.

# Author Model
class Author(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    profile_pic = models.ImageField(default="default-profile-pic.png", upload_to='uploads/profile-pictures', null=True)

    def __str__(self):
        return self.user.username

# Ads Model
class Ads(models.Model):

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        DEAL_PENDING = 'DEAL_PENDING', 'Deal pending'
        SOLD = 'SOLD', 'Sold'
        ARCHIVED = 'ARCHIVED', 'Archived'
    
    CONDITION = (
        ('Brand New', 'Brand New'),
        ('Like New', 'Like New'),
        ('Good', 'Good'),
        ('Fair', 'Fair'),
        ('Needs Repair', 'Needs Repair'),
    )

    author = models.ForeignKey(Author, on_delete=models.CASCADE, null=True)
    title = models.CharField(max_length=200)
    description = RichTextField()
    price = models.DecimalField(max_digits=14, decimal_places=2)
    date_created = models.DateTimeField(auto_now_add=True)
    state = models.ForeignKey('State', on_delete=models.CASCADE, null=True, blank=True)
    city = models.ForeignKey('City', on_delete=models.CASCADE, null=True, blank=True)
    area = models.CharField(max_length=200, blank=True, null=True)
    seller_name = models.CharField(max_length=150, blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.CASCADE, null=True) 
    condition = models.CharField(max_length=100, choices=CONDITION)
    brand = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=50)
    is_phone_verified = models.BooleanField(default=False)
    video = EmbedVideoField(null=True, blank=True) 
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_flagged_hidden = models.BooleanField(default=False)
    view_count = models.PositiveIntegerField(default=0)

    # Common Optional Fields
    is_negotiable = models.BooleanField(default=False)
    purchase_year = models.CharField(max_length=50, blank=True, null=True)
    reason_for_selling = models.CharField(max_length=300, blank=True, null=True)
    bill_or_warranty = models.CharField(max_length=150, blank=True, null=True)
    exchange_accepted = models.BooleanField(default=False)
    preferred_contact = models.CharField(max_length=50, default='Any', blank=True, null=True)
    delivery_available = models.CharField(max_length=50, default='Pickup Only', blank=True, null=True)

    # Category-Specific Extra Fields (Dynamic JSON dictionary)
    extra_details = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name_plural = "Classified Ads"

    def __str__(self):
        return self.title

# State Model
class State(models.Model):
    state_name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, null=True)

    # overriding save method to add slug field from state name if not provided
    def save(self, *args, **kwargs):
        if not self.slug and self.state_name:
            self.slug = slugify(self.state_name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "States"

    def __str__(self):
        return self.state_name

# City Model
class City(models.Model):
    city_name = models.CharField(max_length=100)
    slug = models.SlugField(blank=True, null=True)

    # overriding save method to add slug field from city name if not provided
    def save(self, *args, **kwargs):
        if not self.slug and self.city_name:
            self.slug = slugify(self.city_name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Cities"

    def __str__(self):
        return self.city_name

# Category Model
class Category(models.Model):
    category_name = models.CharField(max_length=150)
    category_image = models.ImageField(upload_to='uploads/category', blank=True, null=True)
    slug = models.SlugField(max_length=150, blank=True, null=True, unique=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    icon_class = models.CharField(max_length=80, blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # overriding save method to add slug field from category name if not provided
    def save(self, *args, **kwargs):
        if not self.slug and self.category_name:
            base_slug = slugify(self.category_name)
            if self.parent:
                base_slug = f"{slugify(self.parent.category_name)}-{base_slug}"
            slug = base_slug[:140]
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug[:130]}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        if self.parent:
            return f"{self.parent.category_name} > {self.category_name}"
        return self.category_name

# Image Model
class AdsImages(models.Model):
    ads = models.ForeignKey(Ads, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='uploads/%Y/%m/%d', default=None)

    def __str__(self):
        return self.ads.title

    class Meta:
        verbose_name_plural = 'Classified Ads Images'

    def save(self, *args, **kwargs):
        if self.image and not self.image._committed:
            try:
                with Image.open(self.image.file) as source:
                    if source.width * source.height > 50_000_000:
                        raise ValidationError('Image dimensions must not exceed 50 megapixels.')
                    image = ImageOps.exif_transpose(source).convert('RGB')
                    image.thumbnail((1440, 1080), Image.Resampling.LANCZOS)
                    output = BytesIO()
                    image.save(output, format='WEBP', quality=82, method=6)
            except (OSError, UnidentifiedImageError) as error:
                raise ValidationError('Upload a valid JPEG, PNG, or WebP image.') from error

            self.image.save(
                f'{uuid.uuid4().hex}.webp',
                ContentFile(output.getvalue()),
                save=False,
            )

        super().save(*args, **kwargs)


class Wishlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    ad = models.ForeignKey(Ads, on_delete=models.CASCADE, related_name='wishlist_items')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['user', 'ad'], name='unique_user_wishlist_ad'),
        ]

    def __str__(self):
        return f'{self.user} saved {self.ad}'


class Offer(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        COUNTERED = 'COUNTERED', 'Countered'
        ACCEPTED = 'ACCEPTED', 'Accepted'
        REJECTED = 'REJECTED', 'Rejected'
        CANCELLED = 'CANCELLED', 'Cancelled'
        EXPIRED = 'EXPIRED', 'Expired'

    ad = models.ForeignKey(Ads, on_delete=models.CASCADE, related_name='offers')
    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='offers_made')
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    counter_amount = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['ad', 'status'])]

    def __str__(self):
        return f'{self.amount} offer for {self.ad}'


class ChatMessage(models.Model):
    ad = models.ForeignKey(Ads, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='marketplace_messages')
    body = models.CharField(max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']
        indexes = [models.Index(fields=['ad', 'created_at'])]

    def __str__(self):
        return f'Message from {self.sender} about {self.ad}'


class ListingReport(models.Model):
    class Reason(models.TextChoices):
        SUSPICIOUS = 'SUSPICIOUS', 'Suspicious or fraudulent'
        COUNTERFEIT = 'COUNTERFEIT', 'Counterfeit'
        MISLEADING = 'MISLEADING', 'Misleading information'
        PROHIBITED = 'PROHIBITED', 'Prohibited item'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending review'
        RESOLVED = 'RESOLVED', 'Resolved'
        DISMISSED = 'DISMISSED', 'Dismissed'

    ad = models.ForeignKey(Ads, on_delete=models.CASCADE, related_name='reports')
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listing_reports')
    reason = models.CharField(max_length=20, choices=Reason.choices)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['ad', 'reporter'], name='unique_reporter_per_ad'),
        ]

    def __str__(self):
        return f'{self.get_reason_display()} report for {self.ad}'


class UserAuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marketplace_actions',
    )
    subject = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marketplace_audit_entries',
    )
    ad = models.ForeignKey(Ads, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_entries')
    action = models.CharField(max_length=60)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['action', 'created_at'])]

    def __str__(self):
        return f'{self.action} at {self.created_at}'


# Top Banner Model
class AdsTopBanner(models.Model):
    title = models.CharField(max_length=200, default="Place Your Ad", blank=True)
    image = models.ImageField(upload_to='banners/%Y/%m/%d', default=None)

    def __str__(self):
        return self.title

# Right Banner Model
class AdsRightBanner(models.Model):
    title = models.CharField(max_length=200, default="Place Your Ad", blank=True)
    image = models.ImageField(upload_to='banners/%Y/%m/%d', default=None)

    def __str__(self):
        return self.title

# Bottom Banner Model
class AdsBottomBanner(models.Model):
    title = models.CharField(max_length=200, default="Place Your Ad", blank=True)
    image = models.ImageField(upload_to='banners/%Y/%m/%d', default=None)

    def __str__(self):
        return self.title

    



    
    
