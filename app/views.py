from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import DestinationDetail, VehicleDetails, SignUpForm, TransporterDetails, TransporterToken, Bid, LOADING_TYPES, WebPushSubscription, ProposedOffer
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
import pytz
from datetime import timedelta
from bidding_app.settings import TIME_ZONE
from datetime import datetime
from django.utils import timezone
from django.db import models
from django.db.models import Count
import uuid
from django.utils.crypto import get_random_string
from django.urls import reverse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from push_notifications.models import WebPushDevice
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from pywebpush import webpush, WebPushException
from django.views.decorators.http import require_POST
from decouple import config
from django.db.models import Sum
import openpyxl
from django.http import HttpResponse
import calendar

from twilio.rest import Client
account_sid = config('account_sid')
auth_token = config('auth_token')
client = Client(account_sid, auth_token)

def send_push_notification(subscription_info, data):
    try:
        webpush(
            subscription_info=subscription_info,
            data=data,  # Ensure data is already serialized as JSON
            vapid_private_key=settings.WEBPUSH_SETTINGS['VAPID_PRIVATE_KEY'],
            vapid_claims={
                "sub": "mailto:{}".format(settings.WEBPUSH_SETTINGS['VAPID_ADMIN_EMAIL'])
            }
        )
    except WebPushException as ex:
        print(f"I'm sorry, Dave, but I can't do that: {repr(ex)}")
        if ex.response and ex.response.json():
            extra = ex.response.json()
            print(f"Remote service replied with a {extra['code']}:{extra['errno']}, {extra['message']}")



def save_web_push_info(request):
    if request.method == 'POST':
        subscription_info = json.loads(request.body.decode('utf-8'))
        endpoint = subscription_info.get('endpoint')
        keys = subscription_info.get('keys', {})
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')
        
        if not all([endpoint, p256dh, auth]):
            return JsonResponse({'status': 'failed', 'message': 'Incomplete subscription info'})


        WebPushSubscription.objects.update_or_create(
            user=request.user,
            endpoint=endpoint,
            defaults={'p256dh': p256dh, 'auth': auth}
        )
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed', 'message': 'Invalid request method'})


def generate_unique_reference(bid_id):
    return f'SEL/TRP/{str(bid_id).zfill(3)}'

@login_required
def create_bid(request):
    if request.method == 'POST':
        # Extract data from the form
        pickup = request.POST['pickup']
        destination = request.POST['destination']
        number_of_vehicles = request.POST['number_of_vehicles']
        time_limit = request.POST['time_limit']
        destination_link = request.POST['destination_link']
        # Create a new DestinationDetail object
        new_bid = DestinationDetail(
            user=request.user,
            pickup=pickup,
            destination=destination,
            number_of_vehicles=number_of_vehicles,
            time_limit=time_limit,
            destination_link=destination_link
        )

        # Save the object to generate an ID
        new_bid.save()

        # Generate the unique reference
        new_bid.reference = generate_unique_reference(new_bid.id)
        new_bid.save()

        return redirect('configure_vehicle', destination_id=new_bid.id, vehicle_index=1)
    else:
        tz = pytz.timezone('Asia/Kolkata')
        default_time_limit =  datetime.now(tz) + timedelta(hours=2)
        default_time_limit_str = default_time_limit.strftime('%Y-%m-%dT%H:%M')
    return render(request, 'create_bid.html', context={'groups': True, 'time_limit': default_time_limit_str, 'vapid_public_key':settings.WEBPUSH_SETTINGS['VAPID_PUBLIC_KEY']})
    # return render(request, 'create_bid.html', context={'groups': request.user.groups.filter(name='Bid Creators').exists, 'time_limit': default_time_limit_str, 'vapid_public_key':settings.WEBPUSH_SETTINGS['VAPID_PUBLIC_KEY']})

@login_required
def create_contact(request):
    error_message = None
    page_number = request.GET.get('page', 1)

    if request.method == 'POST':
        transporter_name = request.POST['transporter_name']
        transporter_contact = request.POST['transporter_contact']

        # Check for unique contact number
        if TransporterDetails.objects.filter(transporter_contact=transporter_contact).exists():
            error_message = "Contact number already exists!"
        else:
            transporter_details = TransporterDetails(
                transporter_name=transporter_name,
                transporter_contact=transporter_contact
            )
            transporter_details.save()
            return redirect('create_contact')

    contacts = TransporterDetails.objects.all()

    # Paginate transporters
    paginator = Paginator(contacts, 8)
    contacts = paginator.get_page(page_number)
    
    return render(request, 'create_contact.html', {
        'contacts': contacts,
        'error_message': error_message,
        # 'groups': request.user.groups.filter(name='Bid Creators').exists(),
        'groups': True,
        # 'transporters': transporters_page,
    })

def place_bid_with_token(request, token):
    transporter_token = get_object_or_404(TransporterToken, token=token)
    transporter = transporter_token.transporter
    destination = transporter_token.destination
    vehicles = VehicleDetails.objects.filter(destination_id=destination)

    bid_end_time = destination.time_limit

    # Retrieve existing bids
    bids = Bid.objects.filter(vehicle__in=vehicles, transporter=transporter)
    existing_bids = {bid.vehicle.id: {'amount': bid.amount} for bid in bids}

    print(existing_bids)
    context = {
        'transporter': transporter,
        'destination': destination,
        'vehicles': vehicles,
        'bid_end_time': bid_end_time,
        'existing_bids': existing_bids,
    }
    return render(request, 'place_bid.html', context)


def place_bid(request, destination_id, transporter_id):
    destination = get_object_or_404(DestinationDetail, id=destination_id)
    transporter = get_object_or_404(TransporterDetails, id=transporter_id)
    
    vehicles = VehicleDetails.objects.filter(destination_id=destination)
    
    bid_end_time = destination.time_limit
    print(f"Bid End Time: {bid_end_time}")  # Ensure this prints correctly in the console

    return render(request, 'place_bid.html', {
        'destination': destination,
        'transporter': transporter,
        'vehicles': vehicles,
        'bid_end_time': bid_end_time,
    })

@csrf_exempt
def submit_bid(request, destination_id, transporter_id):
    destination = get_object_or_404(DestinationDetail, id=destination_id)
    transporter = get_object_or_404(TransporterDetails, id=transporter_id)
    if request.method == 'POST':
        vehicle_ids = {}
        bid_amounts = {}
        
        for key, value in request.POST.items():
            if key.startswith('vehicle_id_'):
                vehicle_id = key.split('_')[2]  # Extract vehicle id from the key
                vehicle_ids[vehicle_id] = value
            elif key.startswith('bid_amount_'):
                vehicle_id = key.split('_')[2]  # Extract vehicle id from the key
                bid_amounts[vehicle_id] = value

        for vehicle_id in vehicle_ids:
            if vehicle_id in bid_amounts and bid_amounts[vehicle_id]:  # Check if bid_amount is present
                vehicle = get_object_or_404(VehicleDetails, id=vehicle_ids[vehicle_id])
                
                # Check if bid already exists
                bid, created = Bid.objects.update_or_create(
                    vehicle=vehicle,
                    transporter=transporter,
                    defaults={'amount': bid_amounts[vehicle_id]}
                )
                
                # Send web push notification
                devices = WebPushSubscription.objects.filter(user=destination.user)
                for device in devices:
                    subscription = {
                        "endpoint": device.endpoint,
                        "keys": {
                            "p256dh": device.p256dh,
                            "auth": device.auth
                        }
                    }
                    message = {
                        "head": "New Bid",
                        "body": f"{transporter.transporter_name} has posted a bid of ₹{bid_amounts[vehicle_id]} for {vehicle.material_description}",
                        "icon": "/static/icons/icon-512x512.png",
                        "url": f"{settings.SITE_URL}/user_bids/"
                    }
                    try:
                        send_push_notification(subscription, json.dumps(message))
                    except WebPushException as ex:
                        print(f"Error sending push notification: {repr(ex)}")
        return redirect('bid_success')  # redirect to a success page

    # Fetch all vehicles associated with the destination
    vehicles = VehicleDetails.objects.filter(destination_id=destination)
    existing_bids = Bid.objects.filter(transporter=transporter, vehicle__in=vehicles)

    return render(request, 'place_bid.html', {
        'destination': destination,
        'transporter': transporter,
        'vehicles': vehicles,
        'existing_bids': existing_bids
    })

def bid_success(request):
    return render(request, 'bid_success.html')

@login_required
def edit_contact(request, contact_id):
    contact = get_object_or_404(TransporterDetails, id=contact_id)

    if request.method == 'POST':
        contact.transporter_name = request.POST['transporter_name']
        new_contact = request.POST['transporter_contact']
        if new_contact != contact.transporter_contact and TransporterDetails.objects.filter(transporter_contact=new_contact).exists():
            error_message = "Contact number already exists!"
            return render(request, 'edit_contact.html', {
                'contact': contact,
                'error_message': error_message
            })
        contact.transporter_contact = new_contact
        contact.save()
        return redirect('create_contact')

    return render(request, 'edit_contact.html', {'contact': contact})

@login_required
def delete_contact(request, contact_id):
    contact = get_object_or_404(TransporterDetails, id=contact_id)
    contact.delete()
    return redirect('create_contact')

@login_required
def delete_bid(request, bid_id):
    bid = get_object_or_404(DestinationDetail, id=bid_id)
    bid.delete()
    return redirect('user_bids')


@login_required
def configure_vehicle(request, destination_id, vehicle_index):
    destination = get_object_or_404(DestinationDetail, id=destination_id)
    number_of_vehicles = destination.number_of_vehicles

    # Try to get existing vehicle details
    try:
        vehicle_details = VehicleDetails.objects.get(destination_id=destination, vehicle_index=vehicle_index)
    except VehicleDetails.DoesNotExist:
        vehicle_details = None

    if request.method == 'POST':
        material_description = request.POST['material_description']
        material_weight = request.POST['material_weight']
        material_height = request.POST['material_height']
        material_width = request.POST['material_width']
        material_length = request.POST['material_length']
        additional_details = request.POST['additional_details']
        delivery_estimation = request.POST['delivery_estimation']
        loading_date = request.POST['loading_date']  # Capture loading date from POST data
        loading_type = request.POST['loading_type']
        destination_location = request.POST['destination']
        destination_link = request.POST['destination_link']
        number_of_vehicles = int(request.POST['number_of_vehicles'])
        pickup = request.POST['pickup']

        if vehicle_details:
            # Update existing vehicle details
            vehicle_details.material_description = material_description
            vehicle_details.material_weight = material_weight
            vehicle_details.material_height = material_height
            vehicle_details.material_width = material_width
            vehicle_details.material_length = material_length
            vehicle_details.additional_details = additional_details
            vehicle_details.delivery_estimation = delivery_estimation
            vehicle_details.loading_date = loading_date  # Update loading date
            vehicle_details.loading_type = loading_type
        else:
            # Create new vehicle details
            vehicle_details = VehicleDetails(
                destination_id=destination,
                vehicle_index=vehicle_index,
                material_description=material_description,
                material_weight=material_weight,
                material_height=material_height,
                material_width=material_width,
                material_length=material_length,
                additional_details=additional_details,
                delivery_estimation=delivery_estimation,
                loading_date=loading_date,  # Set loading date
                loading_type=loading_type,
            )
        vehicle_details.save()

        # Update destination fields if they have changed
        if destination.destination != destination_location:
            destination.destination = destination_location
            destination.save()
    
        if destination.destination_link != destination_link:
            destination.destination_link = destination_link
            destination.save()

        if destination.pickup != pickup:
            destination.pickup = pickup
            destination.save()

        if destination.number_of_vehicles != number_of_vehicles:
            destination.number_of_vehicles = number_of_vehicles
            destination.save()

        next_vehicle_index = vehicle_index + 1
        if next_vehicle_index <= number_of_vehicles:
            return redirect('configure_vehicle', destination_id=destination_id, vehicle_index=next_vehicle_index)
        else:
            return redirect('configure_contact', destination_id=destination_id)

    context = {
        'destination_id': destination_id,
        'vehicle_index': vehicle_index,
        'loading_types': LOADING_TYPES,
        'number_of_vehicles': number_of_vehicles,
        'material_description': vehicle_details.material_description if vehicle_details else '',
        'material_weight': vehicle_details.material_weight if vehicle_details else '',
        'material_height': vehicle_details.material_height if vehicle_details else '',
        'material_width': vehicle_details.material_width if vehicle_details else '',
        'material_length': vehicle_details.material_length if vehicle_details else '',
        'additional_details': vehicle_details.additional_details if vehicle_details else '',
        'delivery_estimation': vehicle_details.delivery_estimation if vehicle_details else '',
        'loading_date': vehicle_details.loading_date.isoformat() if vehicle_details else '',  # Ensure the date is formatted properly
        'loading_type': vehicle_details.loading_type if vehicle_details else '',
        'destination': destination.destination,
        'destination_link': destination.destination_link,
        'pickup': destination.pickup
    }

    return render(request, 'configure_vehicle.html', context)

@login_required
def configure_contact(request, destination_id):
    destination = get_object_or_404(DestinationDetail, id=destination_id)
    search_query = request.GET.get('search', '')
    page_number = request.GET.get('page', 1)

    if request.method == 'POST':
        if 'add_transporter_id' in request.POST:
            transporter_id = request.POST['add_transporter_id']
            transporter = get_object_or_404(TransporterDetails, id=transporter_id)
            destination.transporters.add(transporter)
            destination.save()

        if 'remove_transporter_id' in request.POST:
            transporter_id = request.POST['remove_transporter_id']
            transporter = get_object_or_404(TransporterDetails, id=transporter_id)
            destination.transporters.remove(transporter)    
            destination.save()

        if 'save_contacts' in request.POST:
            # Generate tokens and links
            return redirect('user_bids')

        return redirect('configure_contact', destination_id=destination.id)

    # Retrieve all transporters or filtered transporters
    transporters = TransporterDetails.objects.all()
    if search_query:
        transporters = transporters.filter(transporter_name__icontains=search_query)

    # Paginate transporters
    paginator = Paginator(transporters, 5)
    transporters_page = paginator.get_page(page_number)

    context = {
        'destination_id': destination_id,
        'transporters': transporters_page,
        'selected_users': destination.transporters.all(),
    }
    return render(request, 'configure_contact.html', context)


@login_required
def save_contacts(request, destination_id):
    if request.method == 'POST':
        destination = get_object_or_404(DestinationDetail, id=destination_id)
        selected_users = destination.transporters.all()
        for transporter in selected_users:
            token = get_random_string(64)[:6]
            TransporterToken.objects.create(
                transporter=transporter,
                destination=destination,
                token=token
            )
            link = f"{settings.SITE_URL}{reverse('place_bid_with_token', args=[token])}"
            # Save the link or email it to the transporter

            print(f"Link for {transporter.transporter_name}: {link}")
            # client.messages.create(from_=config('from_number'),to=f'+91{transporter.transporter_contact}', body=f'Click on this url to place your bid: {link}.')

        return redirect('user_bids')
    else:
        return redirect('configure_contact', destination_id=destination_id)

@login_required
def user_bids(request):
    search_query = request.GET.get('q', '').replace(' ', '').lower()
    bids = DestinationDetail.objects.filter(user=request.user).order_by('-time_limit')
    transporters = TransporterDetails.objects.filter(
        models.Q(transporter_name__icontains=search_query),
        models.Q(transporter_contact__icontains=search_query),
    )
    if search_query:
        # Preprocessing fields to remove spaces and make lowercase
        bids = bids.filter(
            models.Q(destination__icontains=search_query) |
            models.Q(reference__icontains=search_query) |
            models.Q(transporters__transporter_name__iregex=r'{}.*'.format(search_query)) |
            models.Q(transporters__transporter_contact__iregex=r'{}.*'.format(search_query))
        ).distinct()
    
    current_time = timezone.now()
    
    bids = bids.annotate(num_transporters=Count('transporters'))

    for bid in bids:
        time_left = bid.time_limit - current_time
        if time_left.total_seconds() > 0:
            bid.time_left_days = time_left.days
            bid.time_left_hours = time_left.seconds // 3600
            bid.time_left_minutes = (time_left.seconds % 3600) // 60
            bid.time_left_seconds = time_left.seconds % 60
        else:
            bid.time_left_days = None
            bid.time_left_hours = None
            bid.time_left_minutes = None
            bid.time_left_seconds = None

    # Pagination logic
    paginator = Paginator(bids, 15)
    page = request.GET.get('page', 1)
    
    try:
        bids_page = paginator.page(page)
    except PageNotAnInteger:
        bids_page = paginator.page(1)
    except EmptyPage:
        bids_page = paginator.page(paginator.num_pages)
    
    return render(request, 'user_bids.html', {'bids': bids_page, 'current_time': current_time, 'search_query': search_query})


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.refresh_from_db()  # load the profile instance created by the signal
            user.profile.email = form.cleaned_data.get('email')
            user.profile.first_name = form.cleaned_data.get('first_name')
            user.profile.last_name = form.cleaned_data.get('last_name')
            user.save()
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=user.username, password=raw_password)
            login(request, user)
            return redirect('login')
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('create_bid')
    else:
        form = AuthenticationForm()
    signup_form = UserCreationForm()
    return render(request, 'registration/login.html', {'form': form, 'signup_form': signup_form})

@login_required
def specific_bid(request, destination_id):
    destination_obj = get_object_or_404(DestinationDetail, user=request.user, id=destination_id)
    vehicles_obj = VehicleDetails.objects.filter(destination_id=destination_obj)
    vehicle_bids_count = {vehicle.id: Bid.objects.filter(vehicle=vehicle).count() for vehicle in vehicles_obj}

    # Fetching transporters and summing up the amounts of all vehicles for the destination
    transporter_amounts = {}
    for transporter in destination_obj.transporters.all():
        total_amount = Bid.objects.filter(
            vehicle__destination_id=destination_obj,
            transporter=transporter
        ).aggregate(total_amount=Sum('amount'))['total_amount'] or 0
        
        # Fetching the final accepted amount and is_accepted flag from the ProposedOffer model
        proposed_offer = ProposedOffer.objects.filter(
            transporter=transporter,
            destination=destination_obj
        ).first()
        
        final_amount = proposed_offer.new_amount if proposed_offer else 0
        is_accepted = proposed_offer.is_accepted if proposed_offer else False
        is_proposed = proposed_offer.is_proposed if proposed_offer else False
        is_offer_accepted = proposed_offer.is_offer_accepted if proposed_offer else False

        transporter_amounts[transporter] = {
            'total_amount': total_amount,
            'final_amount': final_amount,
            'is_accepted': is_accepted,
            'is_proposed': is_proposed,
            'is_offer_accepted': is_offer_accepted
        }
    
    return render(request, 'specific_bid.html', {
        'destination': destination_obj,
        'vehicles': vehicles_obj,
        'vehicle_bids_count': vehicle_bids_count,
        'transporter_amounts': transporter_amounts,
    })



@login_required
def vehicle_bids(request, vehicle_id):
    vehicle = get_object_or_404(VehicleDetails, id=vehicle_id)
    bids = Bid.objects.filter(vehicle=vehicle).order_by('amount')
    
    # Get transporters linked to the destination
    transporters = vehicle.destination_id.transporters.all()

    # Create a dictionary to map transporters to their bids (if any)
    transporter_bids = {}
    for transporter in transporters:
        transporter_bids[transporter] = bids.filter(transporter=transporter).first()

    return render(request, 'vehicle_bids.html', {
        'vehicle': vehicle,
        'transporter_bids': transporter_bids
    })


@require_POST
@login_required
def accept_transporter_offer(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        transporter_id = data.get('transporter_id')
        destination_id = data.get('destination_id')
        final_amount = data.get('amount')

        transporter = get_object_or_404(TransporterDetails, id=transporter_id)
        destination = get_object_or_404(DestinationDetail, id=destination_id)

        # Set all other offers for this destination to not accepted
        ProposedOffer.objects.filter(destination=destination).update(is_accepted=False, is_proposed=False)

        # Get or create the offer to be accepted
        proposed_offer, created = ProposedOffer.objects.get_or_create(
            transporter=transporter,
            destination=destination,
            # defaults={'new_amount': final_amount},
        )

        if not created:
            proposed_offer.new_amount = final_amount

        proposed_offer.is_accepted = True
        proposed_offer.new_amount = final_amount
        proposed_offer.accepted_by = request.user
        proposed_offer.accepted_at = timezone.now()
        proposed_offer.save()

        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

@require_POST
@login_required
def submit_new_offer(request):
    data = json.loads(request.body)
    transporter_id = data.get('transporter_id')
    new_offer = data.get('new_offer')
    destination_id = data.get('destination_id')

    transporter = TransporterDetails.objects.get(id=transporter_id)
    destination = get_object_or_404(DestinationDetail, id=destination_id)

    # Set all other offers for this destination to not accepted and not proposed
    ProposedOffer.objects.filter(destination=destination).update(is_accepted=False, is_proposed=False)

    # Create or update the proposed offer
    proposed_offer, created = ProposedOffer.objects.get_or_create(
        transporter=transporter,
        destination=destination,
        defaults={'new_amount': new_offer},
    )

    if not created:
        proposed_offer.new_amount = new_offer

    proposed_offer.is_proposed = True
    proposed_offer.is_accepted = False  # Newly proposed offer should not be accepted yet
    proposed_offer.save()

    # Generate token and link
    token = get_random_string(64)[:6]
    TransporterToken.objects.create(
        transporter=transporter,
        destination=destination,
        token=token
    )
    link = f"{settings.SITE_URL}{reverse('offer_response', args=[token])}"

    # Send the link via SMS or email
    client.messages.create(
        from_=config('from_number'),
        to=f'+91{transporter.transporter_contact}',
        body=f'Click on this url to accept or reject the offer: {link}.'
    )

    return JsonResponse({'status': 'success'})


@require_POST
@login_required
def revoke_offer(request):
    data = json.loads(request.body)
    destination_id = data.get('destination_id')
    transporter_id = data.get('transporter_id')

    transporter = TransporterDetails.objects.get(id=transporter_id)
    destination = get_object_or_404(DestinationDetail, id=destination_id)

    # Set all other offers for this destination to not accepted and not proposed
    ProposedOffer.objects.filter(destination=destination, transporter=transporter).update(is_accepted=False, is_proposed=False)
    return JsonResponse({'status': 'success'})


def handle_offer_response(request, token):
    transporter_token = get_object_or_404(TransporterToken, token=token)
    transporter = transporter_token.transporter
    destination = transporter_token.destination

    offer = get_object_or_404(ProposedOffer, transporter=transporter, destination=destination, is_proposed=True)
    # Get all vehicles associated with the destination
    vehicles = VehicleDetails.objects.filter(destination_id=destination)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'accept':
            offer.is_accepted = True
            offer.is_offer_accepted = True
            offer.is_proposed = False
            offer.accepted_at = timezone.now()
            offer.save()

            # Make sure all other offers are marked as not accepted
            ProposedOffer.objects.filter(destination=destination).exclude(id=offer.id).update(is_accepted=False)

            devices = WebPushSubscription.objects.filter(user=destination.user)
            for device in devices:
                subscription = {
                    "endpoint": device.endpoint,
                    "keys": {
                        "p256dh": device.p256dh,
                        "auth": device.auth
                    }
                }
                message = {
                    "head": "New Bid",
                    "body": f"{transporter.transporter_name} has accepted your offer!",
                    "icon": "/static/icons/icon-512x512.png",
                    "url": f"{settings.SITE_URL}/bid/{destination.id}"
                }
                try:
                    send_push_notification(subscription, json.dumps(message))
                except WebPushException as ex:
                    print(f"Error sending push notification: {repr(ex)}")
            return render(request, 'thank_you.html')

        elif action == 'reject':
            offer.is_proposed = False
            offer.is_offer_accepted = False
            offer.is_accepted = False
            offer.save()
            return render(request, 'thank_you.html')

    context = {
        'transporter': transporter,
        'destination': destination,
        'offer': offer,
        'vehicles': vehicles,
    }
    return render(request, 'offer_response.html', context)

@login_required
def generate_report(request):
    current_date = datetime.today()  # Now it uses the correct method
    current_year = current_date.year
    current_month = current_date.month

    # Calculate the next month and year
    if current_month == 12:
        next_month = 1
        next_year = current_year + 1
    else:
        next_month = current_month + 1
        next_year = current_year

    year_range = range(current_year - 5, current_year + 6)  # Example year range

    context = {
        'current_year': current_year,
        'current_month': f'{current_month:02}',  # Format as 01, 02, etc.
        'next_year': next_year,
        'next_month': f'{next_month:02}',
        'year_range': year_range,
    }
    return render(request, 'generate_report.html', context)

@login_required
def download_report(request):
    start_month = int(request.POST.get('start_month'))
    end_month = int(request.POST.get('end_month'))
    start_year = int(request.POST.get('start_year'))
    end_year = int(request.POST.get('end_year'))

    # Calculate the last day of the end month
    _, last_day_of_end_month = calendar.monthrange(end_year, end_month)
    
    # Convert start and end dates to datetime objects for filtering
    start_date = datetime(start_year, start_month, 1)
    end_date = datetime(end_year, end_month, last_day_of_end_month)

    # Create a new Excel workbook and sheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Detailed Report"

    # Write the headers
    headers = [
        "Destination", "Transporter Name", "Total Bid Amount", 
        "Offer Amount", "Material Description", "Loading Date"
    ]
    ws.append(headers)

    # Query the data based on the filtered dates
    destinations = DestinationDetail.objects.all()
    for destination in destinations:
        transporters = destination.transporters.all()

        for transporter in transporters:
            bids = Bid.objects.filter(
                transporter=transporter,
                vehicle__destination_id=destination,
                created_at__range=[start_date, end_date]
            )
            total_bid_amount = bids.aggregate(total=models.Sum('amount'))['total'] or 0

            proposed_offers = ProposedOffer.objects.filter(
                transporter=transporter,
                destination=destination,
                created_at__range=[start_date, end_date]
            )
            offer_amount = proposed_offers.aggregate(total=models.Sum('new_amount'))['total'] or 0

            for bid in bids:
                row = [
                    destination.destination,  # Destination Name
                    transporter.transporter_name,  # Transporter Name
                    total_bid_amount,  # Total Bid Amount
                    offer_amount,  # Offer Amount
                    bid.vehicle.material_description,  # Material Description
                    bid.vehicle.loading_date,  # Loading Date
                ]
                ws.append(row)

    # Generate the response with the Excel file
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename=report_{start_month}_{start_year}_to_{end_month}_{end_year}.xlsx'
    wb.save(response)
    return response
