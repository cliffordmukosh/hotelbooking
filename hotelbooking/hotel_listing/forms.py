from django import forms

class RoomSearchForm(forms.Form):
    room_type = forms.CharField(max_length=50, required=False, label="Room Type")
    capacity_adults = forms.IntegerField(min_value=1, required=False, label="Adults Capacity")
    capacity_children = forms.IntegerField(min_value=0, required=False, label="Children Capacity")
    price_per_night = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Max Price Per Night")
    
    
    
from django import forms
from .models import Guest

class GuestProfileForm(forms.ModelForm):
    class Meta:
        model = Guest
        fields = ['first_name', 'last_name', 'email', 'phone']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2a6f97]'}),
            'last_name': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2a6f97]'}),
            'email': forms.EmailInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2a6f97]'}),
            'phone': forms.TextInput(attrs={'class': 'w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#2a6f97]'}),
        }


from django import forms
from django.contrib.auth.forms import PasswordChangeForm

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        common_classes = (
            "w-full p-3 border-2 border-gray-400 rounded-lg bg-gray-50 text-base "
            "focus:outline-none focus:ring-4 focus:ring-[#2a6f97]/50 placeholder-gray-500"
        )

        self.fields['old_password'].widget = forms.PasswordInput(
            attrs={
                'class': common_classes,
                'placeholder': 'Enter current password',
            }
        )
        self.fields['new_password1'].widget = forms.PasswordInput(
            attrs={
                'class': common_classes,
                'placeholder': 'Enter new password',
            }
        )
        self.fields['new_password2'].widget = forms.PasswordInput(
            attrs={
                'class': common_classes,
                'placeholder': 'Confirm new password',
            }
        )
