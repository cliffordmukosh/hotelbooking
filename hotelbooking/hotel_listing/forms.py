from django import forms

class RoomSearchForm(forms.Form):
    room_type = forms.CharField(max_length=50, required=False, label="Room Type")
    capacity_adults = forms.IntegerField(min_value=1, required=False, label="Adults Capacity")
    capacity_children = forms.IntegerField(min_value=0, required=False, label="Children Capacity")
    price_per_night = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Max Price Per Night")