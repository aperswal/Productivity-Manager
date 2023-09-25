from __future__ import print_function
import datetime
import os.path
import pytz
from dateutil import parser
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/calendar']


def initialize_credentials():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def main():
    creds = initialize_credentials()
    commitHours(creds)
    fetchEvents(creds)

def commitHours(creds):
    try:
        service = build('calendar', 'v3', credentials=creds)
        
        chicago_tz = pytz.timezone('America/Chicago')
        today = datetime.date.today()
        today_chicago = chicago_tz.localize(datetime.datetime(today.year, today.month, today.day))
        
        timeStart = today_chicago.isoformat()
        timeEnd = (today_chicago + datetime.timedelta(hours=23, minutes=59, seconds=59)).isoformat()
        
        print("Getting today's scheduled hours")
        events_result = service.events().list(calendarId='primary', timeMin=timeStart,
                                                timeMax=timeEnd, singleEvents=True,
                                                orderBy='startTime', timeZone='America/Chicago').execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return
        
        total_duration = datetime.timedelta(
            seconds=0,
            minutes=0,
            hours=0,
        )
        print("Daily Tasks:")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            start_formatted = parser.isoparse(start)
            end_formatted = parser.isoparse(end)
            duration = end_formatted - start_formatted
            
            total_duration += duration
            print(f"{event['summary']}, duration: {duration}")
        print(f"Total productive time: {total_duration}")
        
    except HttpError as error:
        print('An error occurred: %s' % error)
    
def fetchEvents(creds):
    service = build('calendar', 'v3', credentials=creds)
    chicago_tz = pytz.timezone('America/Chicago')
    
    # Fetch events from the start of the day to the end of the day
    today = datetime.date.today()
    start_of_day = chicago_tz.localize(datetime.datetime(today.year, today.month, today.day))
    end_of_day = start_of_day + datetime.timedelta(days=1)
    
    start_of_day_iso = start_of_day.isoformat()
    end_of_day_iso = end_of_day.isoformat()
    
    events_result = service.events().list(calendarId='primary', timeMin=start_of_day_iso, timeMax=end_of_day_iso,
                                            singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    
    return events


def addEvent(creds, start_time, duration, description):
    chicago_tz = pytz.timezone('America/Chicago')
    start = start_time
    end = start + datetime.timedelta(hours=duration)
    
    start_formatted = start.isoformat()
    end_formatted = end.isoformat()
    
    event = {
        'summary': description,
        'start': {
            'dateTime': start_formatted,
            'timeZone': 'America/Chicago',
        },
        'end': {
            'dateTime': end_formatted,
            'timeZone': 'America/Chicago',
        },
    }
    
    service = build('calendar', 'v3', credentials=creds)
    event = service.events().insert(calendarId='primary', body=event).execute()
    print('Event created %s' % (event.get('htmlLink')))

if __name__ == '__main__':
    main()