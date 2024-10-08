from django.shortcuts import render, redirect
from .forms import VenueForm, EventForm, EventFormAdmin
from django.http import HttpResponseRedirect
from django.urls import reverse
import calendar
from calendar import HTMLCalendar
from datetime import datetime
from .models import Event, Venue
# Import User Model from Django
from django.contrib.auth.models import User
from django.utils.datastructures import MultiValueDictKeyError
from django.http import HttpResponse
import csv
from django.contrib import messages

from django.http import FileResponse
import io 
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

# Import Pagination Stuff
from django.core.paginator import Paginator
# Show Events
def show_event(request, event_id):
    event = Event.objects.get(pk=event_id)
    return render(request, 'formsapp/show_event.html', {
        "event": event
    })


# Show Events In A Venue
def venue_events(request, venue_id):
    # Grab the Venue
    venue = Venue.objects.get(id=venue_id)
    # Grab the events from that venue
    events = venue.event_set.all()
    if events:
        return render(request, 'formsapp/venue_events.html', {
            "events": events
    })

    else:
        messages.success(request, "That Venue Has No Events At This Time!")
        return redirect("admin_approval")


# Create Admin Event Approval Page
def admin_approval(request):
    # Get The Venues
    venue_list = Venue.objects.all()
    # Get counts
    event_count = Event.objects.all().count()
    venue_count = Venue.objects.all().count()
    user_count = User.objects.all().count()
    event_list = Event.objects.all().order_by('-event_date')
    if request.user.is_superuser:
        if request.method == "POST":
            id_list = request.POST.getlist('boxes')
            
            # Update the database 
            for x in id_list: 
                Event.objects.filter(pk=int(x)).update(approved=True)


            messages.success(request, "Event List Approval Has Been Updated!")
            return redirect("all_events")

        else:
            return render(request, 'formsapp/admin_approval.html', 
                          {"event_list": event_list, 
                           "event_count": event_count, 
                           "venue_count": venue_count, 
                           "user_count": user_count,
                           "venue_list": venue_list})

    else: 
        messages.success(request, "You are not authorized to view this page!")
        return redirect("index")
    return render(request, 'formsapp/admin_approval.html', {})


# Create My Events Page
def my_events(request):
    if request.user.is_authenticated:
        me = request.user.id
        events = Event.objects.filter(attendees=me)
        return render(request, 'formsapp/my_events.html', {'events': events})


    else:
        messages.success(request, ("You are not authorized to view this Page!"))
        #render redirect('list-events')
        return redirect('index')


# Generate a PDF File Venue List
def venue_pdf(request):
    # Create Bytestream buffer
    buf = io.BytesIO()
    # Create a canvas
    c = canvas.Canvas(buf, pagesize=letter, bottomup=0)
    # Create a text object 
    textobj = c.beginText()
    textobj.setTextOrigin(inch, inch)
    textobj.setFont("Helvetica", 14)

    # Add some lines of text
    # lines = [
    #    "This is line 1",
    #        "This is line 2",
    #     "This is line 3",
    #    "This is line 4",
    #]
    # Designate teh Model
    venues = Venue.objects.all()
    lines = []
    for venue in venues:
        lines.append(venue.name)
        lines.append(venue.address)
        lines.append(venue.zip_code)
        lines.append(venue.phone)
        lines.append(venue.email_address)
        lines.append(" ")

# Loop
    for line in lines:
        textobj.textLine(line)

    # Finish UP
    c.drawText(textobj)
    c.showPage()
    c.save()
    buf.seek(0)
# Reterun something
    return FileResponse(buf, as_attachment=True, filename='venue.pdf')
# Generate csv
def venue_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachement; filename=venues.csv'

    #Create a csv writer
    writer = csv.writer(response)
    # Designate teh Model
    venues = Venue.objects.all()
    
    # Add column headings to the csv file
    writer.writerow(['Venue Name', 'Address', 'Zip Code', 'Phone', 'Web Address', 'Email' ])
    # Loop through and output
    for venue in venues: 
        writer.writerow([venue.name, venue.address, venue.zip_code, venue.phone, venue.web, venue.email_address])
    
    return response

# Generate Text File Venue List
def venue_text(request):
    response = HttpResponse(content_type='text/plain')
    response['Content-Disposition'] = 'attachement; filename=venues.text '
    # Designate teh Model
    venues = Venue.objects.all()
    # Create blank list
    lines = []
    # Loop through and output
    for venue in venues: 
        lines.append(f'{venue.name}\n{venue.address}\n{venue.zip_code}\n{venue.phone}\n{venue.web}\n{venue.email_address}\n\n\n)')
    # lines = ["This is line 1\n",
    # "This is line 2\n",
    # "This is line 3\n"]
    
    # Write to textfile
    response.writelines(lines)
    return response


#   Delete an Event
def delete_venue(request, venue_id):
    venue = Venue.objects.get(pk=venue_id)
    venue.delete()
    #render redirect('list-events')
    return redirect('list-venues')

#   Delete an Event
def delete_event(request, event_id):
    event = Event.objects.get(pk=event_id)
    if request.user == event.manager:
        event.delete()
        messages.success(request, ("Event Deleted!"))
        return redirect('all_events')
    else:
        messages.success(request, ("You are not authorized to delete this event!"))
        #render redirect('list-events')
        return redirect('all_events')

def update_event(request, event_id):
    event = Event.objects.get(pk=event_id)
    if request.user.is_superuser:
        form = EventFormAdmin(request.POST or None, instance=event)
    else:
        form = EventForm(request.POST or None, instance=event)
    
    if form.is_valid():
        form.save()
        return redirect('all_events')
    
    return render(request, 'formsapp/update_event.html', {'event': event,'form':form})


def add_event(request):
    submitted = False
    if request.method == 'POST':
        if request.user.is_superuser:
            form = EventFormAdmin(request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect('/add_event?submitted=True')
                #return HttpResponseRedirect(reverse('add-event'))
        
        else: 
            form = EventFormAdmin(request.POST)
            if form.is_valid():
                #form.save()
                event = form.save(commit=False)
                event.manager = request.user # logged in user
                event.save()                
                return HttpResponseRedirect('/add_event?submitted=True')
                #return HttpResponseRedirect(reverse('add-event'))
        
    else:
        # Just Going To The Page, Not Submitting
        if request.user.is_superuser:
            form = EventFormAdmin
        else:
            form = EventForm

        if 'submitted' in request.GET:
            submitted = True

    return render(request, 'formsapp/add_event.html', {'form': form, 'submitted':submitted})


def update_venue(request, venue_id):    
    venue = Venue.objects.get(pk=venue_id)
    form = VenueForm(request.POST or None, request.FILES or None, instance=venue)
    if form.is_valid():
        form.save()
        return redirect('list-venues')
    

    return render(request, 'formsapp/update_venue.html', {'venue': venue,'form':form})

    
def search_venues(request):
    if request.method == 'POST':
        try:
            searched = request.POST['searched']

            venues = Venue.objects.filter(name__contains=searched)

            return render(request, 
            'formsapp/search_venues.html', 
            {'searched': searched, 'venues': venues})
        except MultiValueDictKeyError:
             return render(request, 'formsapp/search_venues.html', {'error_message': 'Invalid search query.'})
    else:
        return render(request, 
        'formsapp/search_venues.html', 
        {})

def search_events(request):
    if request.method == 'POST':        
            searched = request.POST['searched']
            events = Event.objects.filter(name__contains=searched)
            return render(request, 
            'formsapp/search_events.html', 
            {'searched': searched, 'events': events})
        
    else:
        return render(request, 
        'formsapp/search_events.html', {})

def show_venue(request, venue_id):
    venue = Venue.objects.get(pk=venue_id)
    venue_owner = User.objects.get(pk=venue.owner)
     # Grab the events from that venue
    events = venue.event_set.all()
    return render(request, 'formsapp/show_venue.html', 
                  {'venue': venue, 'venue_owner': venue_owner, 'events': events})
def list_venues(request):
    #venue_list = Venue.objects.all().order_by('-name') # '?' for random
    venue_list = Venue.objects.all()
    # Set up Pagination
    p = Paginator(Venue.objects.all(), 3)
    page = request.GET.get('page')
    venues = p.get_page(page)
    #nums = "a" * venues.paginator.num_pages

    return render(request, 'formsapp/venue.html', 
                  {'venue_list': venue_list, 'venues': venues}) # you can add 'nums': nums
def all_events(request):
    event_list = Event.objects.all().order_by('-event_date')
    return render(request, 'formsapp/all_events.html', 
                  {'event_list': event_list})
def index(request, year=datetime.now().year, month=datetime.now().strftime('%B')):
    month = month.capitalize()
    # Convert month from name to number
    month_number = list(calendar.month_name).index(month)
    month_number = int(month_number)

    # Create a calendar
    now = datetime.now()
    current_year = now.year
    # Query Current year
    event_list = Event.objects.filter(
        event_date__year = year,
        event_date__month = month_number
    )
    # Get current time
    time = now.strftime('%I:%M %p')
    cal = HTMLCalendar().formatmonth(
        year, 
        month_number)
    # Get current year
    return render(request, 
            'formsapp/index.html', {        
            "year": year,
            "month": month,
            "month_number": month_number,
            "cal":cal,
            "current_year": current_year,
            "time": time,
            "event_list": event_list
            })

def add_venue(request):
    submitted = False
    if request.method == 'POST':
        form = VenueForm(request.POST, request.FILES)
        if form.is_valid():
            venue = form.save(commit=False)
            venue.owner = request.user.id # logged in user
            venue.save()
            #form.save()
            #return HttpResponseRedirect('/add_venue?submitted=True')
            return HttpResponseRedirect(reverse('index'))
            
    else:
        form = VenueForm
        if 'submitted' in request.GET:
            submitted = True

    return render(request, 'formsapp/add_venue.html', {'form': form, 'submitted':submitted})
