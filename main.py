import GoogleCalendar
import Notion
import Util

def main():
    # Initialize Google Calendar Credentials
    credentials = Util.get_credentials()

    # Fetch existing events from Google Calendar
    existing_events = Util.get_existing_events(credentials)

    # Fetch tasks and required hours from Notion
    tasks_and_hours = Notion.get_tasks_and_hours()

    # Check if there are enough available hours in the day for tasks
    Util.check_available_hours(tasks_and_hours, existing_events)  # Fixed the line here

    # Schedule tasks fetched from Notion to Google Calendar
    Util.schedule_tasks(credentials)

    # Ensure there are no tasks scheduled around classes
    Util.ensure_no_tasks_around_classes(credentials)

    print("Tasks have been scheduled successfully!")

if __name__ == "__main__":
    main()
