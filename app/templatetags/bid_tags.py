from django import template
from ..models import Bid

register = template.Library()

@register.filter
def get_bid_for_vehicle(transporter, vehicle):
    try:
        bid = Bid.objects.get(transporter=transporter, vehicle=vehicle)
        return bid.amount
    except Bid.DoesNotExist:
        return None
