from django.contrib import admin
from .models import (
    Author,
    Ads,
    State,
    City,
    Category,
    AdsImages,
    AdsTopBanner,
    AdsRightBanner,
    AdsBottomBanner,
    Wishlist,
    Offer,
    ChatMessage,
    ListingReport,
    UserAuditLog,
)
from django.utils.html import format_html

# Register your models here.

class AdsImagesAdmin(admin.StackedInline):
    model = AdsImages

class AdsAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'price', 'author', 'category', 'status', 'is_flagged_hidden', 'report_count', 'date_created')
    list_display_links = ('id', 'title')
    list_filter = ('status', 'is_active', 'is_flagged_hidden', 'is_featured', 'date_created')
    search_fields = ('title', 'description', 'brand', 'author__user__username', 'city__city_name')
    readonly_fields = ('view_count',)
    inlines = [AdsImagesAdmin]

    @admin.display(description='Reports')
    def report_count(self, obj):
        return obj.reports.count()


@admin.register(ListingReport)
class ListingReportAdmin(admin.ModelAdmin):
    list_display = ('id', 'ad', 'reporter', 'reason', 'status', 'created_at')
    list_filter = ('status', 'reason', 'created_at')
    search_fields = ('ad__title', 'reporter__username', 'details')
    readonly_fields = ('ad', 'reporter', 'reason', 'details', 'created_at')
    actions = ('resolve_reports', 'dismiss_reports')

    @admin.action(description='Resolve selected reports')
    def resolve_reports(self, request, queryset):
        queryset.update(status=ListingReport.Status.RESOLVED)

    @admin.action(description='Dismiss selected reports')
    def dismiss_reports(self, request, queryset):
        queryset.update(status=ListingReport.Status.DISMISSED)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('id', 'ad', 'buyer', 'amount', 'counter_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('ad__title', 'buyer__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'ad', 'created_at')
    search_fields = ('user__username', 'ad__title')
    readonly_fields = ('created_at',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'ad', 'sender', 'created_at', 'read_at')
    list_filter = ('created_at', 'read_at')
    search_fields = ('ad__title', 'sender__username', 'body')
    readonly_fields = ('ad', 'sender', 'body', 'created_at', 'read_at')


@admin.register(UserAuditLog)
class UserAuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'action', 'actor', 'subject', 'ad')
    list_filter = ('action', 'created_at')
    search_fields = ('actor__username', 'subject__username', 'ad__title')
    readonly_fields = ('actor', 'subject', 'ad', 'action', 'details', 'created_at')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class AdsImagesAdmin(admin.ModelAdmin):
    pass


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'parent', 'display_order', 'icon_class', 'is_active')
    list_editable = ('display_order', 'icon_class', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('category_name', 'slug')
    prepopulated_fields = {'slug': ('category_name',)}


admin.site.register(Ads, AdsAdmin)
admin.site.register(AdsImages, AdsImagesAdmin)

admin.site.register(Author)
admin.site.register(State)
admin.site.register(City)
admin.site.register(AdsTopBanner)
admin.site.register(AdsRightBanner)
admin.site.register(AdsBottomBanner)
