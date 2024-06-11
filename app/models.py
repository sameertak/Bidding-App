from django.db import models
from django.contrib.auth.models import User
from django import forms 
from django.contrib.auth.forms import UserCreationForm

class DestinationDetail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pickup = models.CharField(max_length=40)
    destination = models.CharField(max_length=40)
    destination_link = models.CharField(max_length=50)
    number_of_vehicles = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    time_limit = models.DateTimeField()
    
LOADING_TYPES = (
    ("ptl", "Part Truck Load"),
    ("ftl", "Full Truck Load")
)

class VehicleDetails(models.Model):
    destination_id = models.ForeignKey("DestinationDetail", on_delete=models.CASCADE)
    material_description = models.TextField()
    vehicle_index = models.IntegerField()
    material_weight = models.IntegerField()
    material_height = models.IntegerField()
    material_width = models.IntegerField()
    material_length = models.IntegerField()
    additional_details = models.TextField()
    delivery_estimation = models.IntegerField()
    loading_date = models.DateTimeField()
    loading_type = models.CharField(max_length=5, choices=LOADING_TYPES)  # Ensure this field exists


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'Email'}))
    first_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'First Name'}))
    last_name = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Last Name'}))

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        if commit:
            user.save()
        return user
