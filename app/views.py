from django.shortcuts import render, redirect, get_object_or_404
from .models import DestinationDetail, VehicleDetails, CustomUserCreationForm, LOADING_TYPES
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

@login_required
def create_bid(request):
    if request.method == 'POST':
        pickup = request.POST['pickup']
        destination = request.POST['destination']
        number_of_vehicles = int(request.POST['number_of_vehicles'])
        destination_link = request.POST['destination_link']
        time_limit = request.POST['time_limit']
        
        destination_detail = DestinationDetail(
            user=request.user,
            pickup=pickup,
            destination=destination,
            destination_link=destination_link,
            number_of_vehicles=number_of_vehicles,
            time_limit=time_limit,
        )
        destination_detail.save()
        return redirect('configure_vehicle', destination_id=destination_detail.id, vehicle_index=1)
    return render(request, 'create_bid.html', context={'groups': request.user.groups.filter(name='Bid Creators').exists})


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
        loading_date = request.POST['loading_date']
        loading_type = request.POST['loading_type']

        if vehicle_details:
            # Update existing vehicle details
            vehicle_details.material_description = material_description
            vehicle_details.material_weight = material_weight
            vehicle_details.material_height = material_height
            vehicle_details.material_width = material_width
            vehicle_details.material_length = material_length
            vehicle_details.additional_details = additional_details
            vehicle_details.delivery_estimation = delivery_estimation
            vehicle_details.loading_date = loading_date
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
                loading_date=loading_date,
                loading_type=loading_type,
            )
        vehicle_details.save()

        next_vehicle_index = vehicle_index + 1
        if next_vehicle_index <= number_of_vehicles:
            return redirect('configure_vehicle', destination_id=destination_id, vehicle_index=next_vehicle_index)
        else:
            return redirect('some_final_view')  # Replace with the appropriate final view

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
        'loading_date': vehicle_details.loading_date.isoformat() if vehicle_details else '',
        'loading_type': vehicle_details.loading_type if vehicle_details else '',
    }

    return render(request, 'configure_vehicle.html', context)

@login_required
def user_bids(request):
    bids = DestinationDetail.objects.filter(user=request.user)
    return render(request, 'user_bids.html', {'bids': bids})

def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect('create_bid')
    else:
        form = CustomUserCreationForm()
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
