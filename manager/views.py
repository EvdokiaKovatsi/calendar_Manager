from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout

from .forms import ImportForm, ExportForm

from apiclient import discovery
import google.oauth2.credentials

import csv


SCOPES = ['https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events',
    'https://www.googleapis.com/auth/calendar.events.readonly']

GMT_OFF = '+02:00' #Athens/GMT +2

calendar_choices = {}
page_token = None

# Create your views here.


def index(request):
    msg = 'hi'

    context = {
        'current': msg
        if request.user.is_authenticated else[]
    }

    return render(request, 'manager/index.html', context)

@login_required
def importCSV(request):
    page_token = None
    errorMessage = False


    if request.method == 'POST':

        GCAL = build_calendar(request)
        form = ImportForm(request.POST, request.FILES, my_arg=calendar_choices.items())
        if form.is_valid():
            fileCSV = request.FILES['upload_csv']

            if fileCSV.name.endswith('.csv'):

                decoded_file = fileCSV.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)

                user_calendar = form.cleaned_data['calendar_choices']

                for row in reader:
                    event = populate_calendar(row)
                    e = GCAL.events().insert(calendarId=user_calendar, sendNotifications=False,
                        body=event).execute()

    else:

        GCAL = build_calendar(request)

        calendar_choices.clear()
        while True:

            calendar_list = GCAL.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                calendar_choices.update({calendar_list_entry['id']: calendar_list_entry['summary']})
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break

        form = ImportForm(my_arg=calendar_choices.items())


    context = {
        'form': form,
        'errorMessage': errorMessage

    }
    return render(request, 'manager/importCSV.html', context)

@login_required
def exportCalendar(request):

    page_token = None
    if request.method == 'POST':

        GCAL = build_calendar(request)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename = "calendar.csv"'

        form = ExportForm(request.POST, my_arg=calendar_choices.items())
        writer = csv.writer(response)

        if form.is_valid():
            user_calendar = form.cleaned_data['calendar_choices']
            date_Max = form.cleaned_data['timeMax']
            date_Min = form.cleaned_data['timeMin']

            stringMin = str(date_Min).replace(' ','T')
            stringMax = str(date_Max).replace(' ','T')

            events = GCAL.events().list(calendarId=user_calendar,
                timeMin=stringMin,
                timeMax=stringMax,
                singleEvents=True,
                orderBy='startTime').execute()


            writer.writerow(['event_name', 'date', 'start', 'end', 'attendees', 'location', 'description'])


            for event in events['items']:
                start = event['start'].get('dateTime', event['start'].get('dateTime'))
                temp = start.split('T')
                date = temp[0]
                start = temp[1].split('+')
                end = event['end'].get('dateTime', event['end'].get('dateTime'))
                temp = end.split('T')
                end = temp[1].split('+')
                if 'attendees' in event:
                    attendees = ''
                    for attendee in event['attendees']:
                        attendees += attendee.get('email', attendee.get('email'))
                        attendees += ' '
                else:
                    attendees = 'none'

                if 'location' in event:
                    location = event['location']
                else:
                    location = ''

                if 'description' in event:
                    description = event['description']
                else:
                    description = ' '
                writer.writerow([event['summary'], date, start[0],
                        end[0], attendees, location, description])

        else:
            print('here')
        return response

    else:

        GCAL = build_calendar(request)

        calendar_choices.clear()
        while True:

            calendar_list = GCAL.calendarList().list(pageToken=page_token).execute()
            for calendar_list_entry in calendar_list['items']:
                calendar_choices.update({calendar_list_entry['id']: calendar_list_entry['summary']})
            page_token = calendar_list.get('nextPageToken')
            if not page_token:
                break

        form = ExportForm(my_arg=calendar_choices.items())

        context = {
            'form' : form

            }
        return render(request, 'manager/exportCalendar.html', context)

def helpPage(request):

    return render(request, 'manager/helpPage.html')

def logoutView(request):
    logout(request)
    return render(request, 'manager/index.html')

#    EVENT = {
#        'summary': 'Dinner with friends',
#        'start': {'dateTime': '2018-11-22T15:00:00%s' % GMT_OFF},
#        'end': {'dateTime': '2018-11-22T18:00:00%s' % GMT_OFF},
#    }
#"""
#CREATING EVENT NOTES
#-if more than one email in attendees throws error. Create an if that checks
#if there are more than one attendee and if so makes the string into a list
#called attendees[].
#-Dates that there should not be events at. Modify/Delete events in these
#days.
#"""
#Timestamps require the format: "YYYY-MM-DDTHH:MM:SS+GMT_OFF"

def populate_calendar(csv_row):


    EVENT = {
        'summary': csv_row['event_name'],
        'start': {
            'dateTime': csv_row['date']+'T'+csv_row['start']+':00',
            'timeZone' : 'Europe/Athens'
        },
        'end': {
            'dateTime': csv_row['date']+'T'+csv_row['end']+':00',
            'timeZone' : 'Europe/Athens'},

        'location': csv_row['location'],
        'description': csv_row['description'],
    }
    if csv_row['professors'] != '':
        temp = []
        professors = csv_row['professors'].split(',')

        for professor in professors:
            professor = professor.replace(' ','')
            temp.append({'email': professor})
        #'attendees': [{ 'email' : csv_row['professors'] }],
        EVENT['attendees'] = temp

    if csv_row['recurrence'] != '':
        until = csv_row['recurrence'].replace('-','')
        recurrence = ['RRULE:FREQ=WEEKLY;UNTIL='+until+'T230000Z']
        EVENT['recurrence'] = recurrence

    return EVENT

def build_calendar(request):

    user = request.user
    social = user.social_auth.get(provider='google-oauth2')

    creds = google.oauth2.credentials.Credentials(social.extra_data['access_token'])
    #GCAL = discovery.build('calendar', 'v3', http=creds.authorize(Http()))
    GCAL = discovery.build('calendar', 'v3', credentials = creds)
    return GCAL
