from django import forms
from ckeditor.widgets import CKEditorWidget
from .models import *

class PostAdsForm(forms.ModelForm):
    title = forms.CharField(widget=forms.TextInput(attrs={
        'type': 'text',
        'class': 'form-control',  
        'name': 'title', 
        'placeholder': 'Title'
    }))

    description = forms.CharField(widget=CKEditorWidget(attrs={
        'type': 'text',
        'class': 'form-control',  
        'name': 'description', 
        'placeholder': 'Description'
    }))

    price = forms.CharField(widget=forms.NumberInput(attrs={
        'class': 'form-control',  
        'name': 'price', 
        'placeholder': 'Price'
    }))

    city = forms.CharField(widget=forms.TextInput(attrs={
        'type': 'text',
        'class': 'form-control',  
        'name': 'city', 
        'placeholder': 'City'
    }))

    brand = forms.CharField(widget=forms.TextInput(attrs={
        'type': 'text',
        'class': 'form-control',  
        'name': 'brand', 
        'placeholder': 'Brand'
    }))

    phone = forms.CharField(widget=forms.TextInput(attrs={
        'type': 'text',
        'class': 'form-control',  
        'name': 'phone', 
        'placeholder': 'Phone'
    }))

    class Meta:
        model = Ads
        fields = '__all__'
        exclude = ['author', 'date_created', 'is_featured']
    

    
    
class AdsEditForm(forms.ModelForm):
    class Meta:
        model = Ads
        fields = (
            'title',
            'description',
            'price',
            'category',
            'condition',
            'state',
            'city',
            'area',
            'seller_name',
            'phone',
            'brand',
            'video',
            'is_negotiable',
            'purchase_year',
            'reason_for_selling',
            'bill_or_warranty',
            'exchange_accepted',
            'preferred_contact',
            'delivery_available',
            'extra_details',
        )
        widgets = {
            'description': CKEditorWidget(),
            'extra_details': forms.Textarea(attrs={'rows': 4, 'placeholder': 'JSON object of additional specifications'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True).order_by('display_order', 'category_name')
        self.fields['state'].queryset = State.objects.order_by('state_name')
        self.fields['city'].queryset = City.objects.order_by('city_name')
        for field in self.fields.values():
            field.widget.attrs.setdefault('class', 'form-control')
        