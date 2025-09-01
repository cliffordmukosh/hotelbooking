from django.contrib import admin
from django.core.exceptions import ValidationError
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    Room, Guest, Booking, BookingGuest,
    Meal, MealPreference, Payment
)


# 🔹 Base class to make rows clickable
class ClickableRowAdmin(admin.ModelAdmin):
    class Media:
        js = ("hotel_listing/admin_row_click.js",)
        css = {"all": ("hotel_listing/admin_row_click.css",)}


# 🔸 Room Admin
@admin.register(Room)
class RoomAdmin(ClickableRowAdmin):
    list_display = (
        "room_number", "room_type", "bed_type", "capacity_adults",
        "capacity_children", "price_per_night", "is_available", "image"
    )
    list_filter = ("room_type", "bed_type", "is_available")
    search_fields = ("room_number", "room_type", "bed_type", "description")
    ordering = ("room_number",)
    readonly_fields = ("image_preview",)

    fieldsets = (
        (None, {
            "fields": (
                "room_number", "room_type", "bed_type",
                "capacity_adults", "capacity_children",
                "price_per_night", "is_available"
            )
        }),
        ("Additional Information", {
            "fields": ("description", "image", "image_preview"),
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" style="max-height: 200px; max-width: 200px;" />'
        return "No image available"
    image_preview.allow_tags = True
    image_preview.short_description = "Image Preview"


# 🔸 Guest Admin
@admin.register(Guest)
class GuestAdmin(ClickableRowAdmin):
    list_display = ("first_name", "last_name", "email", "phone")
    search_fields = ("first_name", "last_name", "email", "phone")
    ordering = ("last_name", "first_name")


# 🔸 Inlines for Booking
class BookingGuestInline(admin.TabularInline):
    model = BookingGuest
    extra = 1


class MealPreferenceInline(admin.TabularInline):
    model = MealPreference
    extra = 1
    autocomplete_fields = ['meal']


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 1


# 🔸 Booking Form with Validation
class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        room = cleaned_data.get("room")
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        num_adults = cleaned_data.get("num_adults", 0)
        num_children = cleaned_data.get("num_children", 0)

        # Validate date order
        if start_date and end_date and end_date <= start_date:
            raise ValidationError(_("End date must be after start date."))

        if room:
            # Capacity check
            if num_adults > room.capacity_adults or num_children > room.capacity_children:
                raise ValidationError(
                    _(f"Room capacity exceeded. Max: {room.capacity_adults} adults, {room.capacity_children} children.")
                )

            # Overlapping booking check
            overlapping = Booking.objects.filter(
                room=room,
                start_date__lt=end_date,
                end_date__gt=start_date
            ).exclude(pk=self.instance.pk)

            if overlapping.exists():
                raise ValidationError(
                    _("This room is already booked for the selected date range.")
                )

        return cleaned_data


# 🔸 Booking Admin
@admin.register(Booking)
class BookingAdmin(ClickableRowAdmin):
    form = BookingForm
    list_display = (
        "id", "primary_guest", "room", "start_date", "end_date",
        "num_adults", "num_children", "total_price", "booking_status", "created_at"
    )
    list_filter = ("booking_status", "start_date", "end_date", "created_at")
    search_fields = (
        "id", "primary_guest__first_name",
        "primary_guest__last_name", "room__room_number"
    )
    ordering = ("-created_at",)
    inlines = [BookingGuestInline, MealPreferenceInline, PaymentInline]


# 🔸 Booking Guest Admin
@admin.register(BookingGuest)
class BookingGuestAdmin(ClickableRowAdmin):
    list_display = ("booking", "guest", "is_child")
    list_filter = ("is_child",)
    search_fields = ("booking__id", "guest__first_name", "guest__last_name")


# 🔸 Meal Admin
@admin.register(Meal)
class MealAdmin(ClickableRowAdmin):
    list_display = ("name", "price")
    search_fields = ("name",)
    ordering = ("name",)


# 🔸 Meal Preference Admin
@admin.register(MealPreference)
class MealPreferenceAdmin(ClickableRowAdmin):
    list_display = ("booking", "get_meal_name", "selected")
    list_filter = ("selected", "meal")
    search_fields = ("booking__id", "booking__primary_guest__first_name", "meal__name")

    def get_meal_name(self, obj):
        return obj.meal.name
    get_meal_name.short_description = "Meal"


# 🔸 Payment Admin
@admin.register(Payment)
class PaymentAdmin(ClickableRowAdmin):
    list_display = (
        "id", "booking", "amount", "payment_method",
        "payment_status", "payment_date", "transaction_id"
    )
    list_filter = ("payment_method", "payment_status", "payment_date")
    search_fields = (
        "transaction_id", "booking__id",
        "booking__primary_guest__first_name", "booking__primary_guest__last_name"
    )
    ordering = ("-payment_date",)


# 🔸 Admin site customization
admin.site.site_header = "Hotel Booking Administration"
admin.site.site_title = "Hotel Booking Admin"
admin.site.index_title = "Welcome to Hotel Booking Admin"
