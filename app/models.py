from django.db import models
from django.contrib.auth.models import User
from django import forms 
from django.contrib.auth.forms import UserCreationForm

LOADING_TYPES = (
    ("ptl", "Part Truck Load"),
    ("ftl", "Full Truck Load")
)

class VehicleDetails(models.Model):
    destination_id = models.ForeignKey("DestinationDetail", on_delete=models.CASCADE)
    material_description = models.CharField(max_length=20)
    vehicle_index = models.IntegerField()
    material_weight = models.IntegerField()
    material_height = models.IntegerField()
    material_width = models.IntegerField()
    material_length = models.IntegerField()
    additional_details = models.TextField()
    delivery_estimation = models.IntegerField()
    loading_date = models.DateField()
    loading_type = models.CharField(max_length=5, choices=LOADING_TYPES)  # Ensure this field exists

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


class TransporterDetails(models.Model):
    transporter_name = models.CharField(max_length=25)
    transporter_contact = models.BigIntegerField(unique=True)

class DestinationDetail(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    pickup = models.TextField()
    destination = models.TextField()
    destination_link = models.TextField()
    number_of_vehicles = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    time_limit = models.DateTimeField()
    duration = models.DurationField(null=True, blank=True)
    reference = models.CharField(max_length=20, unique=True, blank=True, null=True)
    transporters = models.ManyToManyField(TransporterDetails)

    def __str__(self):
        return self.reference if self.reference else super().__str__()


class TransporterToken(models.Model):
    transporter = models.ForeignKey(TransporterDetails, on_delete=models.CASCADE)
    destination = models.ForeignKey(DestinationDetail, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.transporter.transporter_name} - {self.token}"


class Bid(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    )
    vehicle = models.ForeignKey('VehicleDetails', on_delete=models.CASCADE)
    transporter = models.ForeignKey('TransporterDetails', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    # status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    # accepted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='accepted_bids')

    def __str__(self):
        return f"Bid by {self.transporter.transporter_name} for {self.vehicle.material_description} - ₹{self.amount}"
    

class WebPushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    endpoint = models.CharField(max_length=500)
    p256dh = models.CharField(max_length=100)
    auth = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class ProposedOffer(models.Model):
    transporter = models.ForeignKey(TransporterDetails, on_delete=models.CASCADE)
    destination = models.ForeignKey(DestinationDetail, on_delete=models.CASCADE)
    new_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # New fields to track acceptance
    is_accepted = models.BooleanField(default=False)
    is_offer_accepted = models.BooleanField(default=False)
    # accepted_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    accepted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    is_proposed = models.BooleanField(default=False)  # New field
