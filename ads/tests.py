import json
import tempfile
from decimal import Decimal
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Ads, AdsImages, Category, City, ListingReport, Offer, State


class MarketplaceWorkflowTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.seller = user_model.objects.create_user(username='seller', password='safe-password-123')
        self.buyer = user_model.objects.create_user(username='buyer', password='safe-password-123')
        self.other_buyer = user_model.objects.create_user(username='buyer-two', password='safe-password-123')
        self.third_buyer = user_model.objects.create_user(username='buyer-three', password='safe-password-123')
        self.category = Category.objects.create(category_name='Electronics')
        self.state = State.objects.create(state_name='Gujarat')
        self.city = City.objects.create(city_name='Ahmedabad')
        self.ad = Ads.objects.create(
            author=self.seller.author,
            title='Used camera',
            description='A camera in good condition.',
            price=Decimal('1000.00'),
            category=self.category,
            condition='Good',
            state=self.state,
            city=self.city,
            phone='9999999999',
        )

    def json_post(self, url, payload):
        return self.client.post(url, data=json.dumps(payload), content_type='application/json')

    def test_homepage_renders_with_local_images_and_database_content(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Good finds.')
        self.assertContains(response, 'backpack.jpg')
        self.assertContains(response, 'Used camera')

    def test_live_feed_returns_only_new_public_listings(self):
        sold_ad = Ads.objects.create(
            author=self.seller.author,
            title='Already sold',
            description='Not available.',
            price=Decimal('10.00'),
            category=self.category,
            condition='Good',
            phone='9999999999',
            status=Ads.Status.SOLD,
        )
        response = self.client.get(reverse('api-live-feed'), {'after_id': 0})
        self.assertEqual(response.status_code, 200)
        items = response.json()['items']
        self.assertIn(self.ad.pk, [item['id'] for item in items])
        self.assertNotIn(sold_ad.pk, [item['id'] for item in items])

    def test_search_api_filters_by_price_and_city(self):
        response = self.client.get(reverse('api-listings'), {
            'min_price': '900',
            'max_price': '1100',
            'city': 'ahmed',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.json()['results']], [self.ad.pk])

    def test_search_listing_detail_and_edit_pages_render(self):
        response = self.client.get(reverse('ads-search'), {'customword': 'camera', 'city': 'Ahmedabad'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Used camera')

        response = self.client.get(reverse('ads-detail', args=[self.ad.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Message about this item')

        self.client.force_login(self.seller)
        response = self.client.get(reverse('ads-edit', args=[self.ad.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Edit listing')

    def test_user_listing_and_wishlist_pages_render(self):
        from .models import Wishlist

        Wishlist.objects.create(user=self.buyer, ad=self.ad)
        self.client.force_login(self.buyer)
        self.assertEqual(self.client.get(reverse('profile-favorite-ads')).status_code, 200)
        self.client.force_login(self.seller)
        self.assertEqual(self.client.get(reverse('profile-ads')).status_code, 200)

    def test_wishlist_toggle_saves_and_removes(self):
        self.client.force_login(self.buyer)
        url = reverse('api-wishlist-toggle', args=[self.ad.pk])
        saved = self.json_post(url, {})
        self.assertEqual(saved.status_code, 200)
        self.assertTrue(saved.json()['saved'])
        removed = self.json_post(url, {})
        self.assertEqual(removed.status_code, 200)
        self.assertFalse(removed.json()['saved'])
        self.assertEqual(self.ad.wishlist_items.count(), 0)

    def test_seller_can_counter_offer_and_buyer_can_accept(self):
        self.client.force_login(self.buyer)
        response = self.json_post(reverse('api-offer-create', args=[self.ad.pk]), {'amount': '800'})
        self.assertEqual(response.status_code, 201)
        offer_id = response.json()['id']

        self.client.force_login(self.seller)
        counter = self.json_post(reverse('api-offer-respond', args=[offer_id]), {
            'decision': 'COUNTER',
            'amount': '900',
        })
        self.assertEqual(counter.status_code, 200)
        self.assertEqual(counter.json()['status'], Offer.Status.COUNTERED)

        self.client.force_login(self.buyer)
        accepted = self.json_post(reverse('api-offer-respond', args=[offer_id]), {'decision': 'ACCEPT'})
        self.assertEqual(accepted.status_code, 200)
        self.ad.refresh_from_db()
        self.assertEqual(self.ad.status, Ads.Status.DEAL_PENDING)
        self.assertEqual(self.ad.offers.get(pk=offer_id).status, Offer.Status.ACCEPTED)

    def test_three_independent_reports_hide_listing(self):
        users = [self.buyer, self.other_buyer, self.third_buyer]
        for index, user in enumerate(users):
            self.client.force_login(user)
            response = self.json_post(reverse('api-listing-report', args=[self.ad.pk]), {
                'reason': ListingReport.Reason.SUSPICIOUS,
                'details': f'Report {index}',
            })
            self.assertEqual(response.status_code, 201)
        self.ad.refresh_from_db()
        self.assertTrue(self.ad.is_flagged_hidden)

    def test_chat_is_limited_to_participants_and_tracks_read_receipts(self):
        url = reverse('api-chat-messages', args=[self.ad.pk])
        self.assertEqual(self.client.get(url).status_code, 401)
        self.client.force_login(self.third_buyer)
        self.assertEqual(self.client.get(url).status_code, 403)
        self.client.force_login(self.buyer)
        sent = self.json_post(reverse('api-chat-send', args=[self.ad.pk]), {'body': 'Is this still available?'})
        self.assertEqual(sent.status_code, 201)

        self.client.force_login(self.seller)
        messages_response = self.client.get(reverse('api-chat-messages', args=[self.ad.pk]))
        self.assertEqual(messages_response.status_code, 200)
        self.assertEqual(messages_response.json()['messages'][0]['body'], 'Is this still available?')
        self.assertIsNotNone(self.ad.chat_messages.first().read_at)

    def test_uploaded_images_are_sanitized_and_converted_to_webp(self):
        self.temp_media = tempfile.TemporaryDirectory()
        media_settings = override_settings(MEDIA_ROOT=self.temp_media.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)
        self.addCleanup(self.temp_media.cleanup)

        source = Image.new('RGB', (1800, 1200), color='blue')
        exif = Image.Exif()
        exif[274] = 6
        image_buffer = BytesIO()
        source.save(image_buffer, format='JPEG', exif=exif)
        uploaded = SimpleUploadedFile('camera.jpg', image_buffer.getvalue(), content_type='image/jpeg')
        listing_image = AdsImages.objects.create(ads=self.ad, image=uploaded)

        with Image.open(listing_image.image.path) as processed:
            self.assertEqual(processed.format, 'WEBP')
            self.assertLessEqual(processed.width, 1440)
            self.assertLessEqual(processed.height, 1080)
            self.assertEqual(len(processed.getexif()), 0)
