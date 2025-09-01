from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path("book/<int:room_id>/", views.book_room, name="book_room"),
    path("confirm/<int:room_id>/", views.confirm_booking, name="confirm_booking"),

    # Authentication
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("add-payment/<int:booking_id>/", views.add_payment, name="add_payment"),
    
    # ... existing URLs ...
    path('booking/<int:booking_id>/', views.booking_details, name='booking_details'),
    path('receipt/<int:booking_id>/', views.print_receipt, name='print_receipt'),
    
    
]

