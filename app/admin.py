# admin.py
from django.contrib import admin
from .models import VehicleDetails, TransporterDetails, DestinationDetail, TransporterToken, Bid, WebPushSubscription

# Custom admin class for VehicleDetails
class VehicleDetailsAdmin(admin.ModelAdmin):
    list_display = ('destination_id', 'material_description', 'vehicle_index', 'material_weight', 'material_height', 'material_width', 'material_length', 'loading_date', 'loading_type')
    search_fields = ('material_description', 'loading_type')
    list_filter = ('loading_date', 'loading_type')

# Custom admin class for TransporterDetails
class TransporterDetailsAdmin(admin.ModelAdmin):
    list_display = ('transporter_name', 'transporter_contact')
    search_fields = ('transporter_name',)

# Custom admin class for DestinationDetail
class DestinationDetailAdmin(admin.ModelAdmin):
    list_display = ('user', 'pickup', 'destination', 'destination_link', 'number_of_vehicles', 'created_at', 'time_limit', 'reference')
    search_fields = ('pickup', 'destination', 'reference')
    list_filter = ('created_at', 'time_limit')

# Custom admin class for TransporterToken
class TransporterTokenAdmin(admin.ModelAdmin):
    list_display = ('transporter', 'destination', 'token', 'created_at')
    search_fields = ('token',)
    list_filter = ('created_at',)

# Custom admin class for Bid
class BidAdmin(admin.ModelAdmin):
    list_display = ('vehicle', 'transporter', 'amount', 'created_at')
    search_fields = ('vehicle__material_description', 'transporter__transporter_name')
    list_filter = ('created_at',)

# Custom admin class for WebPushSubscription
class WebPushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint', 'created_at')
    search_fields = ('user__username', 'endpoint')
    list_filter = ('created_at',)

# Register the models with their custom admin classes
admin.site.register(VehicleDetails, VehicleDetailsAdmin)
admin.site.register(TransporterDetails, TransporterDetailsAdmin)
admin.site.register(DestinationDetail, DestinationDetailAdmin)
admin.site.register(TransporterToken, TransporterTokenAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(WebPushSubscription, WebPushSubscriptionAdmin)
