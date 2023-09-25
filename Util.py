import datetime
from dateutil import parser
import GoogleCalendar
import Notion
import pytz


def get_credentials():
    return GoogleCalendar.initialize_credentials()

def get_existing_events(credentials):
    return GoogleCalendar.fetchEvents(credentials)

def get_tasks_and_hours():
    return Notion.get_tasks_and_hours()

def check_available_hours(tasks_and_hours, existing_events):
    # Fetch wake up and sleep events and calculate available hours
    # Print out existing events for debugging
    print("Existing Events:")
    for event in existing_events:
        print(event['summary'])
    
    wake_up_event = next((event for event in existing_events if event['summary'].strip() == 'Wake Up'), None)
    sleep_event = next((event for event in existing_events if event['summary'].strip() == 'Sleep'), None)

    if not wake_up_event or not sleep_event:
        print("Wake Up or Sleep events not found!")
        return
    
    wake_up_time = parser.isoparse(wake_up_event['start']['dateTime'])
    sleep_time = parser.isoparse(sleep_event['start']['dateTime'])
    available_hours = (sleep_time - wake_up_time).total_seconds() / 3600
    
    total_hours_needed = sum(tasks_and_hours.values())
    if total_hours_needed > available_hours:
        print("Warning: Overbooking! Reduce tasks or hours.")



def find_next_free_slot(existing_events, current_time, end_time):
    chicago_tz = pytz.timezone('America/Chicago')
    for event in existing_events:
        event_start = parser.isoparse(event['start']['dateTime']).astimezone(chicago_tz)
        event_end = parser.isoparse(event['end']['dateTime']).astimezone(chicago_tz)
        if event_start < current_time:
            continue
        if event_start >= end_time:
            return current_time, end_time
        if current_time < event_start:
            return current_time, event_start
        current_time = max(current_time, event_end)
    return current_time, end_time


def schedule_tasks(credentials):
    chicago_tz = pytz.timezone('America/Chicago')
    
    existing_events = get_existing_events(credentials)
    
    wake_up_event = min((event for event in existing_events if event['summary'].strip() == 'Wake Up' and parser.isoparse(event['end']['dateTime']).astimezone(chicago_tz) > datetime.datetime.now(chicago_tz)), key=lambda x: parser.isoparse(x['end']['dateTime']).astimezone(chicago_tz), default=None)
    
    if wake_up_event is None:
        print("Wake Up event not found!")
        return
    
    sleep_event = min((event for event in existing_events if event['summary'].strip() == 'Sleep' and parser.isoparse(event['start']['dateTime']).astimezone(chicago_tz) > parser.isoparse(wake_up_event['end']['dateTime']).astimezone(chicago_tz)), key=lambda x: parser.isoparse(x['start']['dateTime']).astimezone(chicago_tz), default=None)
    
    if sleep_event is None:
        print("Sleep event not found!")
        return
    
    wake_up_time = parser.isoparse(wake_up_event['end']['dateTime']).astimezone(chicago_tz)
    sleep_time = parser.isoparse(sleep_event['start']['dateTime']).astimezone(chicago_tz)
    
    current_time = max(datetime.datetime.now(chicago_tz), wake_up_time)
    if current_time >= sleep_time:
        print("Not enough time left in the day to schedule tasks.")
        return
    
    tasks_and_hours = get_tasks_and_hours()
    
    for task, duration in tasks_and_hours.items():
        remaining_duration = duration
        while remaining_duration > 0:
            current_time, next_event_start = find_next_free_slot(existing_events, current_time, sleep_time)
            
            available_time = (next_event_start - current_time).total_seconds() / 3600
            if available_time >= remaining_duration:
                GoogleCalendar.addEvent(credentials, current_time, remaining_duration, task)
                current_time += datetime.timedelta(hours=remaining_duration)
                remaining_duration = 0
            else:
                GoogleCalendar.addEvent(credentials, current_time, available_time, task + " - Part 1")
                current_time = next_event_start
                remaining_duration -= available_time
            
            if current_time >= sleep_time or remaining_duration <= 0:
                break
    
    if (sleep_time - current_time).total_seconds() / 3600 < 2:
        print("Warning: Less than 2 hours break after scheduling all tasks!")


def ensure_no_tasks_around_classes(credentials):
    existing_events = get_existing_events(credentials)
    class_events = [event for event in existing_events if "Class" in event['summary']]
    other_events = [event for event in existing_events if "Class" not in event['summary']]
    
    for class_event in class_events:
        class_start = parser.isoparse(class_event['start']['dateTime'])
        class_end = parser.isoparse(class_event['end']['dateTime'])
        
        # Check if there are any events scheduled 2 hours before or after class
        for other_event in other_events:
            other_start = parser.isoparse(other_event['start']['dateTime'])
            other_end = parser.isoparse(other_event['end']['dateTime'])
            
            # Check if the other event is within 2 hours before or after the class
            if other_start < class_start and (class_start - other_end).total_seconds() < 7200:
                print(f"Warning: Event {other_event['summary']} is less than 2 hours before {class_event['summary']}")
            elif other_end > class_end and (other_start - class_end).total_seconds() < 7200:
                print(f"Warning: Event {other_event['summary']} is less than 2 hours after {class_event['summary']}")
