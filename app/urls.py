from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('create_bid/', views.create_bid, name='create_bid'),
    path('configure_vehicle/<int:destination_id>/<int:vehicle_index>/', views.configure_vehicle, name='configure_vehicle'),
    path('user_bids/', views.user_bids, name='user_bids'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('signup/', views.signup, name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),
]