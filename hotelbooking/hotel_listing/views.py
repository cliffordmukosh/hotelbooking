from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Q, Sum
from django.utils.dateparse import parse_date
from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Room, Booking, Guest, BookingGuest, Meal, MealPreference, Payment
from django.template.loader import render_to_string
from django.http import HttpResponse
import pdfkit
import datetime

from django.shortcuts import render
from django.db.models import Q, F
from datetime import datetime as dt  # Alias datetime class to avoid confusion
from .models import Room, Booking

def home(request):
    rooms = Room.objects.filter(is_available=True)

    checkin = request.GET.get('checkin')
    checkout = request.GET.get('checkout')
    adults = request.GET.get('adults')
    children = request.GET.get('children')
    num_rooms = request.GET.get('rooms')
    room_type = request.GET.get('room_type')
    bed_type = request.GET.get('bed_type')

    if checkin and checkout:
        checkin_date = dt.strptime(checkin, '%Y-%m-%d').date() if checkin else None
        checkout_date = dt.strptime(checkout, '%Y-%m-%d').date() if checkout else None

        if checkin_date and checkout_date:
            booked_rooms = Booking.objects.filter(
                Q(start_date__lt=checkout_date),
                Q(end_date__gt=checkin_date),
                booking_status="Confirmed"
            ).values_list('room_id', flat=True)

            rooms = rooms.exclude(id__in=booked_rooms)

    if adults and adults.isdigit():
        rooms = rooms.filter(capacity_adults__gte=int(adults))
    if children and children.isdigit():
        rooms = rooms.filter(capacity_children__gte=int(children))
    if num_rooms and num_rooms.isdigit():
        if hasattr(Room, "total_rooms"):
            rooms = rooms.filter(total_rooms__gte=int(num_rooms))

    if room_type:
        rooms = rooms.filter(room_type__iexact=room_type)
    if bed_type:
        rooms = rooms.filter(bed_type__iexact=bed_type)

    context = {
        "rooms": rooms,
        "error": request.GET.get('error')
    }
    return render(request, "home.html", context)

def book_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    meals = Meal.objects.all()

    checkin = request.GET.get("checkin")
    checkout = request.GET.get("checkout")
    adults = request.GET.get("adults")
    children = request.GET.get("children")
    rooms = request.GET.get("rooms")
    selected_meals = request.GET.getlist("meals")

    if not checkin or not checkout or not adults:
        return redirect(f"{reverse('home')}?error=Please+fill+in+check-in,+check-out,+and+adults+fields")

    try:
        adults = int(adults) if adults and adults.isdigit() else 1
        children = int(children) if children and children.isdigit() else 0
        rooms = int(rooms) if rooms and rooms.isdigit() else 1
    except ValueError:
        return redirect(f"{reverse('home')}?error=Invalid+input+for+adults,+children,+or+rooms")

    checkin_date = parse_date(checkin)
    checkout_date = parse_date(checkout)
    if not checkin_date or not checkout_date or checkout_date <= checkin_date:
        return redirect(f"{reverse('home')}?error=Invalid+check-in+or+check-out+date")

    context = {
        "room": room,
        "meals": meals,
        "checkin": checkin,
        "checkout": checkout,
        "adults": adults,
        "children": children,
        "rooms": rooms,
        "selected_meals": selected_meals,
    }
    return render(request, "book_room.html", context)

def confirm_booking(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    meals = Meal.objects.all()

    checkin = request.GET.get("checkin")
    checkout = request.GET.get("checkout")
    adults = request.GET.get("adults")
    children = request.GET.get("children")
    rooms = request.GET.get("rooms")
    selected_meals = request.GET.getlist("meals")

    if not checkin or not checkout or not adults:
        return redirect(f"{reverse('home')}?error=Please+fill+in+check-in,+check-out,+and+adults+fields")

    try:
        adults = int(adults) if adults and adults.isdigit() else 1
        children = int(children) if children and children.isdigit() else 0
        rooms = int(rooms) if rooms and rooms.isdigit() else 1
    except ValueError:
        return redirect(f"{reverse('home')}?error=Invalid+input+for+adults,+children,+or+rooms")

    checkin_date = parse_date(checkin)
    checkout_date = parse_date(checkout)
    if not checkin_date or not checkout_date or checkout_date <= checkin_date:
        return redirect(f"{reverse('home')}?error=Invalid+check-in+or+check-out+date")

    if request.method == "POST":
        if adults > room.capacity_adults * rooms or children > room.capacity_children * rooms:
            return render(request, "confirm_booking.html", {
                "room": room, "meals": meals, "checkin": checkin, "checkout": checkout,
                "adults": adults, "children": children, "rooms": rooms, "selected_meals": selected_meals,
                "error": "Booking exceeds room capacity!"
            })

        if request.user.is_authenticated:
            try:
                primary_guest = request.user.guest_profile
            except Guest.DoesNotExist:
                return render(request, "confirm_booking.html", {
                    "room": room, "meals": meals, "checkin": checkin, "checkout": checkout,
                    "adults": adults, "children": children, "rooms": rooms, "selected_meals": selected_meals,
                    "error": "No guest profile found for this user."
                })
        else:
            password = request.POST.get("password")
            confirm_password = request.POST.get("confirm_password")
            if password != confirm_password:
                return render(request, "confirm_booking.html", {
                    "room": room, "meals": meals, "checkin": checkin, "checkout": checkout,
                    "adults": adults, "children": children, "rooms": rooms, "selected_meals": selected_meals,
                    "error": "Passwords do not match."
                })
            if not password or len(password) < 8:
                return render(request, "confirm_booking.html", {
                    "room": room, "meals": meals, "checkin": checkin, "checkout": checkout,
                    "adults": adults, "children": children, "rooms": rooms, "selected_meals": selected_meals,
                    "error": "Password must be at least 8 characters long."
                })

            username = request.POST.get("username")
            email = request.POST.get("email")
            try:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=request.POST["first_name"],
                    last_name=request.POST["last_name"]
                )
                primary_guest = Guest.objects.create(
                    user=user,
                    first_name=request.POST["first_name"],
                    last_name=request.POST["last_name"],
                    email=email,
                    phone=request.POST.get("phone", "")
                )
            except Exception as e:
                return render(request, "confirm_booking.html", {
                    "room": room, "meals": meals, "checkin": checkin, "checkout": checkout,
                    "adults": adults, "children": children, "rooms": rooms, "selected_meals": selected_meals,
                    "error": f"Error creating primary guest: {str(e)}"
                })

        nights = (checkout_date - checkin_date).days
        room_total = room.price_per_night * nights * rooms
        meal_total = Decimal("0.00")
        for meal_id in request.POST.getlist("meals"):
            try:
                meal = Meal.objects.get(id=meal_id)
                meal_total += meal.price * nights * rooms
            except Meal.DoesNotExist:
                continue
        total_price = room_total + meal_total
        vat_amount = total_price * Decimal("0.18")
        grand_total = total_price + vat_amount

        try:
            booking = Booking.objects.create(
                primary_guest=primary_guest,
                room=room,
                start_date=checkin_date,
                end_date=checkout_date,
                num_adults=adults,
                num_children=children,
                total_price=grand_total,
                booking_status="Pending"
            )
        except Exception as e:
            return render(request, "confirm_booking.html", {
                "room": room, "meals": meals, "checkin": checkin, "checkout": checkout,
                "adults": adults, "children": children, "rooms": rooms, "selected_meals": selected_meals,
                "error": f"Error creating booking: {str(e)}"
            })

        is_primary_guest_in_booking = request.POST.get("is_primary_guest_in_booking") == "on"
        if is_primary_guest_in_booking:
            try:
                BookingGuest.objects.create(booking=booking, guest=primary_guest, is_child=False)
            except Exception as e:
                return render(request, "confirm_booking.html", {
                    "room": room, "meals": meals, "checkin": checkin, "checkout": checkout,
                    "adults": adults, "children": children, "rooms": rooms, "selected_meals": selected_meals,
                    "error": f"Error linking primary guest to booking: {str(e)}"
                })

        required_adults = adults - 1 if is_primary_guest_in_booking else adults
        added_adults = 0
        for i in range(1, required_adults + 1):
            first = request.POST.get(f"adult_{i}_first")
            last = request.POST.get(f"adult_{i}_last")
            email = request.POST.get(f"adult_{i}_email")
            phone = request.POST.get(f"adult_{i}_phone", "")
            if first and last and email:
                try:
                    guest = Guest.objects.create(
                        first_name=first,
                        last_name=last,
                        email=email,
                        phone=phone
                    )
                    BookingGuest.objects.create(booking=booking, guest=guest, is_child=False)
                    added_adults += 1
                except Exception as e:
                    return render(request, "confirm_booking.html", {
                        "room": room, "meals": meals, "checkin": checkin, "checkout": checkout,
                        "adults": adults, "children": children, "rooms": rooms, "selected_meals": selected_meals,
                        "error": f"Error adding adult guest {first} {last}: {str(e)}"
                    })

        added_children = 0
        for i in range(1, children + 1):
            first = request.POST.get(f"child_{i}_first")
            last = request.POST.get(f"child_{i}_last")
            email = request.POST.get(f"child_{i}_email", "")
            phone = request.POST.get(f"child_{i}_phone", "")
            if first and last:
                try:
                    guest = Guest.objects.create(
                        first_name=first,
                        last_name=last,
                        email=email or f"child{i}_{booking.id}@noemail.com",
                        phone=phone
                    )
                    BookingGuest.objects.create(booking=booking, guest=guest, is_child=True)
                    added_children += 1
                except Exception as e:
                    return render(request, "confirm_booking.html", {
                        "room": room, "meals": meals, "checkin": checkin, "checkout": checkout,
                        "adults": adults, "children": children, "rooms": rooms, "selected_meals": selected_meals,
                        "error": f"Error adding child guest {first} {last}: {str(e)}"
                    })

        if added_adults < required_adults or added_children < children:
            return render(request, "confirm_booking.html", {
                "room": room, "meals": meals, "checkin": checkin, "checkout": checkout,
                "adults": adults, "children": children, "rooms": rooms, "selected_meals": selected_meals,
                "error": f"Please provide all required guests. Needed: {required_adults} adult(s), {children} child(ren)."
            })

        for meal_id in request.POST.getlist("meals"):
            try:
                meal = Meal.objects.get(id=meal_id)
                MealPreference.objects.create(booking=booking, meal=meal, selected=True)
            except Meal.DoesNotExist:
                continue

        return redirect("dashboard")

    context = {
        "room": room,
        "meals": meals,
        "checkin": checkin,
        "checkout": checkout,
        "adults": adults,
        "children": children,
        "rooms": rooms,
        "selected_meals": selected_meals,
    }
    return render(request, "confirm_booking.html", context)



def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "login.html")

    return render(request, "login.html")

@login_required
def dashboard(request):
    try:
        guest = request.user.guest_profile
    except Guest.DoesNotExist:
        messages.error(request, "No guest profile found for this user.")
        return redirect("home")

    bookings = guest.bookings.all()
    for booking in bookings:
        total_paid = booking.payments.aggregate(total=Sum("amount"))["total"] or 0
        booking.total_paid = total_paid
        booking.balance = booking.total_price - total_paid
        if total_paid >= booking.total_price:
            booking.payment_status = "Paid"
        elif total_paid > 0:
            booking.payment_status = "Partial"
        else:
            booking.payment_status = "Unpaid"

    return render(request, "dashboard.html", {"guest": guest, "bookings": bookings})

@login_required
def booking_details(request, booking_id):
    try:
        guest = request.user.guest_profile
    except Guest.DoesNotExist:
        messages.error(request, "No guest profile found for this user.")
        return redirect("dashboard")

    booking = get_object_or_404(Booking, id=booking_id, primary_guest=guest)
    return render(request, "booking_details.html", {"booking": booking})


from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.db.models import Q, Sum
from django.utils.dateparse import parse_date
from decimal import Decimal
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Room, Booking, Guest, BookingGuest, Meal, MealPreference, Payment
from django.http import HttpResponse
import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

@login_required
def print_receipt(request, booking_id):
    try:
        guest = request.user.guest_profile
    except Guest.DoesNotExist:
        messages.error(request, "No guest profile found for this user.")
        return redirect("dashboard")

    booking = get_object_or_404(Booking, id=booking_id, primary_guest=guest)
    
    # Calculate payment status
    total_paid = booking.payments.aggregate(total=Sum("amount"))["total"] or 0
    booking.total_paid = total_paid
    booking.balance = booking.total_price - total_paid
    if total_paid >= booking.total_price:
        booking.payment_status = "Paid"
    elif total_paid > 0:
        booking.payment_status = "Partial"
    else:
        booking.payment_status = "Unpaid"

    if booking.payment_status != "Paid":
        messages.error(request, "Receipt can only be generated for fully paid bookings.")
        return redirect("booking_details", booking_id=booking_id)

    nights = (booking.end_date - booking.start_date).days
    room_total = booking.room.price_per_night * nights
    meal_total = sum(pref.meal.price * nights for pref in booking.meal_preferences.filter(selected=True))
    subtotal = room_total + meal_total
    vat_amount = subtotal * Decimal("0.18")
    payments = booking.payments.filter(payment_status="Completed")

    # Create PDF response
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="receipt_booking_{booking.id}.pdf"'

    # Create PDF document
    doc = SimpleDocTemplate(response, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(name='Title', fontSize=18, fontName='Helvetica-Bold', textColor=colors.HexColor('#2a6f97'), alignment=1, spaceAfter=10)
    subtitle_style = ParagraphStyle(name='Subtitle', fontSize=12, fontName='Helvetica', alignment=1, spaceAfter=10)
    section_style = ParagraphStyle(name='Section', fontSize=14, fontName='Helvetica-Bold', textColor=colors.HexColor('#2a6f97'), spaceAfter=5)
    normal_style = ParagraphStyle(name='Normal', fontSize=10, fontName='Helvetica', spaceAfter=6)
    footer_style = ParagraphStyle(name='Footer', fontSize=8, fontName='Helvetica', textColor=colors.HexColor('#666666'), alignment=1, spaceAfter=6)
    dash_style = ParagraphStyle(name='Dash', fontSize=10, fontName='Helvetica', spaceAfter=10, spaceBefore=10)

    # Header
    elements.append(Paragraph("Hotel Booking Receipt", title_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#2a6f97'), spaceAfter=10))
    elements.append(Paragraph(f"Receipt for Booking ID: {booking.id}", subtitle_style))
    elements.append(Paragraph(f"Issued on: {datetime.date.today()}", subtitle_style))
    elements.append(Spacer(1, 0.5*cm))

    # Dashed line separator
    elements.append(Paragraph("------------", dash_style))

    # Guest Information
    elements.append(Paragraph("Guest Information", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc'), spaceAfter=5))
    elements.append(Paragraph(f"Primary Guest: {booking.primary_guest.first_name} {booking.primary_guest.last_name}", normal_style))
    elements.append(Paragraph(f"Email: {booking.primary_guest.email or 'N/A'}", normal_style))
    elements.append(Paragraph(f"Phone: {booking.primary_guest.phone or 'N/A'}", normal_style))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("------------", dash_style))

    # Booking Details
    elements.append(Paragraph("Booking Details", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc'), spaceAfter=5))
    elements.append(Paragraph(f"Room Number: {booking.room.room_number} ({booking.room.room_type})", normal_style))
    elements.append(Paragraph(f"Check-in Date: {booking.start_date}", normal_style))
    elements.append(Paragraph(f"Check-out Date: {booking.end_date}", normal_style))
    elements.append(Paragraph(f"Nights: {nights}", normal_style))
    elements.append(Paragraph(f"Adults: {booking.num_adults}", normal_style))
    elements.append(Paragraph(f"Children: {booking.num_children}", normal_style))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("------------", dash_style))

    # Cost Breakdown
    elements.append(Paragraph("Cost Breakdown", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc'), spaceAfter=5))
    cost_data = [
        ['Description', 'Amount (KSh)'],
        [f"Room Cost ({nights} nights x {booking.room.price_per_night}/night)", f"{room_total:.2f}"],
    ]
    for pref in booking.meal_preferences.filter(selected=True):
        cost_data.append([f"{pref.meal.name} ({nights} nights x {pref.meal.price}/night)", f"{pref.meal.price * nights:.2f}"])
    cost_data.extend([
        ['Subtotal', f"{subtotal:.2f}"],
        ['VAT (18%)', f"{vat_amount:.2f}"],
        ['Grand Total', f"{booking.total_price:.2f}"],
    ])
    cost_table = Table(cost_data, colWidths=[12*cm, 5*cm])
    cost_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a4d6e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
    ]))
    elements.append(cost_table)
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("------------", dash_style))

    # Payment Details
    elements.append(Paragraph("Payment Details", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc'), spaceAfter=5))
    payment_data = [
        ['Payment Method', 'Amount (KSh)', 'Transaction ID', 'Date'],
    ]
    for payment in payments:
        payment_data.append([
            payment.payment_method,
            f"{payment.amount:.2f}",
            payment.transaction_id or 'N/A',
            payment.payment_date.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    payment_table = Table(payment_data, colWidths=[5*cm, 4*cm, 4*cm, 4*cm])
    payment_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a4d6e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
    ]))
    elements.append(payment_table)
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("------------", dash_style))

    # Additional Guests
    elements.append(Paragraph("Additional Guests", section_style))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#cccccc'), spaceAfter=5))
    if booking.booking_guests.exists():
        for booking_guest in booking.booking_guests.all():
            elements.append(Paragraph(
                f"{booking_guest.guest.first_name} {booking_guest.guest.last_name} "
                f"({'Child' if booking_guest.is_child else 'Adult'})",
                normal_style
            ))
    else:
        elements.append(Paragraph("No additional guests.", normal_style))
    elements.append(Spacer(1, 0.5*cm))
    elements.append(Paragraph("------------", dash_style))

    # Footer
    elements.append(Paragraph("Thank you for choosing our hotel!", footer_style))
    elements.append(Paragraph("Contact us at: support@hotel.com | +254 700 123 456", footer_style))
    elements.append(Paragraph(f"Order Created: {booking.created_at.strftime('%Y-%m-%d %H:%M:%S')}", footer_style))
    elements.append(Paragraph(f"Receipt Printed: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", footer_style))

    # Build PDF
    doc.build(elements)
    return response
def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def add_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if Payment.objects.filter(booking=booking).exists():
        messages.warning(request, "Payment already exists for this booking.")
        return redirect("dashboard")

    if request.method == "POST":
        try:
            amount = Decimal(request.POST.get("amount"))
            method = request.POST.get("method")
            transaction_code = request.POST.get("transaction_code", "").strip()
            transaction_id = transaction_code if transaction_code else None
            payment_status = "Completed" if transaction_id else "Pending"

            Payment.objects.create(
                booking=booking,
                amount=amount,
                payment_method=method,
                transaction_id=transaction_id,
                payment_status=payment_status
            )
            messages.success(request, "Payment added successfully.")
            return redirect("dashboard")
        except Exception as e:
            messages.error(request, f"Error adding payment: {str(e)}")
            return render(request, "add_payment.html", {"booking": booking})

    return render(request, "add_payment.html", {"booking": booking})