from django.urls import path

from .views import BookingCreateView, HomeView, LSASearchView, PaymentWebhookView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("api/v1/bookings/", BookingCreateView.as_view(), name="booking-create"),
    path("api/v1/lsas/search/", LSASearchView.as_view(), name="lsa-search"),
    path("api/payments/webhook/", PaymentWebhookView.as_view(), name="payment-webhook"),
]