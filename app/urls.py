from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='create_bid/', permanent=False)),
    path('create_bid/', views.create_bid, name='create_bid'),
    path('configure_vehicle/<int:destination_id>/<int:vehicle_index>/', views.configure_vehicle, name='configure_vehicle'),
    path('user_bids/', views.user_bids, name='user_bids'),
    path('configure_contact/<int:destination_id>/', views.configure_contact, name='configure_contact'),
    path('save_contacts/<int:destination_id>/', views.save_contacts, name='save_contacts'),
    path('create_contact/', views.create_contact, name='create_contact'),
    path('edit_contact/<int:contact_id>/', views.edit_contact, name='edit_contact'),
    path('delete_contact/<int:contact_id>/', views.delete_contact, name='delete_contact'),
    path('delete_bid/<int:bid_id>/', views.delete_bid, name='delete_bid'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('bid/<int:destination_id>', views.specific_bid, name='bid'),
    path('place-bid/<str:token>/', views.place_bid_with_token, name='place_bid_with_token'),
    path('submit-bid/<int:destination_id>/<int:transporter_id>/', views.submit_bid, name='submit_bid'),
    path('bid_success/', views.bid_success, name='bid_success'),
    path('webpush/save_information/', views.save_web_push_info, name='save_web_push_info'),
    path('vehicle/<int:vehicle_id>/bids/', views.vehicle_bids, name='vehicle_bids'),
    path('accept_transporter_offer/', views.accept_transporter_offer, name='Accept Proposed Order'),
    path('submit_new_offer/', views.submit_new_offer, name="submit_new_offer"),
    path('revoke_offer/', views.revoke_offer, name="revoke_offer"),
    path('offer_response/<str:token>/', views.handle_offer_response, name='offer_response'),
    path('generate_report/', views.generate_report, name='generate_report'),
    path('download_report/', views.download_report, name='download_report'),
]