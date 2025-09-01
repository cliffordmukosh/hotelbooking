from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import CheckConstraint, Q, F
from django.contrib.auth.models import User

class Room(models.Model):
    room_number = models.CharField(max_length=10, unique=True)
    room_type = models.CharField(max_length=50)  # e.g., Single, Double, Suite
    capacity_adults = models.IntegerField(validators=[MinValueValidator(1)])
    capacity_children = models.IntegerField(validators=[MinValueValidator(0)])
    price_per_night = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    bed_type = models.CharField(
        max_length=20,
        choices=[
            ('Single', 'Single Bed'),
            ('Double', 'Double Bed'),
            ('Two Singles', 'Two Single Beds')
        ]
    )
    is_available = models.BooleanField(default=True)
    image = models.ImageField(upload_to='rooms/', blank=True, null=True)  # New image field
    description = models.TextField(blank=True, null=True)  # New description field

    class Meta:
        db_table = 'rooms'

    def __str__(self):
        return f"{self.room_number} ({self.room_type}, {self.bed_type})"

# Rest of the models (Guest, Booking, BookingGuest, Meal, MealPreference, Payment) remain unchanged
class Guest(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='guest_profile')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=100, null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    class Meta:
        db_table = 'guests'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Booking(models.Model):
    STATUS_CHOICES = [
        ('Confirmed', 'Confirmed'),
        ('Pending', 'Pending'),
        ('Cancelled', 'Cancelled'),
    ]

    primary_guest = models.ForeignKey(Guest, on_delete=models.CASCADE, null=True, related_name='bookings')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings')
    start_date = models.DateField()
    end_date = models.DateField()
    num_adults = models.IntegerField(validators=[MinValueValidator(1)])
    num_children = models.IntegerField(validators=[MinValueValidator(0)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    booking_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bookings'
        constraints = [
            CheckConstraint(
                check=Q(end_date__gt=F('start_date')),
                name='check_dates'
            ),
            CheckConstraint(
                check=Q(num_adults__gt=0),
                name='check_positive_guests'
            ),
        ]

    def __str__(self):
        return f"Booking {self.id} for {self.primary_guest} in {self.room.room_number}"

class BookingGuest(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_guests')
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='booking_guest_entries')
    is_child = models.BooleanField(default=False)

    class Meta:
        db_table = 'booking_guests'
        unique_together = ('booking', 'guest')

    def __str__(self):
        return f"{self.guest} in Booking {self.booking.id} ({'Child' if self.is_child else 'Adult'})"

class Meal(models.Model):
    name = models.CharField(max_length=50, unique=True)  # e.g., Breakfast, Lunch, Dinner
    price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        db_table = 'meals'

    def __str__(self):
        return f"{self.name} (${self.price})"

class MealPreference(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='meal_preferences')
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE, related_name='meal_preferences')
    selected = models.BooleanField(default=False)

    class Meta:
        db_table = 'meal_preferences'
        unique_together = ('booking', 'meal')

    def __str__(self):
        return f"{self.booking} - {self.meal.name} ({'Selected' if self.selected else 'Not Selected'})"

class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('Cash', 'Cash'),
        ('Online Transfer', 'Online Transfer'),
    ]
    STATUS_CHOICES = [
        ('Completed', 'Completed'),
        ('Pending', 'Pending'),
        ('Failed', 'Failed'),
        ('Refunded', 'Refunded'),
    ]

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_date = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, unique=True, blank=True, null=True)

    class Meta:
        db_table = 'payments'
        constraints = [
            CheckConstraint(
                check=Q(amount__gt=0),
                name='check_positive_amount'
            ),
        ]

    def __str__(self):
        return f"Payment {self.id} for Booking {self.booking.id}"