from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import datetime

SCOPES = ['https://www.googleapis.com/auth/calendar']

# My local timezone — Dubai is UTC+4
LOCAL_TIMEZONE = 'Asia/Dubai'
LOCAL_UTC_OFFSET = 4


def get_calendar_service():
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
    return build('calendar', 'v3', credentials=creds)

# lists the next 10 coming events in google calendar starting from now.
def list_upcoming_events(service, max_results=10):
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return events_result.get('items', [])


def add_event(service, summary, start_iso, end_iso):
    event = {
        'summary': summary,
        'start': {'dateTime': start_iso, 'timeZone': LOCAL_TIMEZONE},
        'end': {'dateTime': end_iso, 'timeZone': LOCAL_TIMEZONE},
    }
    return service.events().insert(calendarId='primary', body=event).execute()


def delete_event(service, event_id):
    service.events().delete(calendarId='primary', eventId=event_id).execute()


def format_event_time(event):
    """Display event time in local Dubai time."""
    start_str = event['start'].get('dateTime', event['start'].get('date'))
    try:
        dt = datetime.datetime.fromisoformat(start_str)
        offset = datetime.timezone(datetime.timedelta(hours=LOCAL_UTC_OFFSET))
        dt_local = dt.astimezone(offset)
        return dt_local.strftime('%Y-%m-%d %I:%M %p')
    except Exception:
        return start_str


def print_events(events):
    if not events:
        print("No upcoming events found.")
        return
    for i, e in enumerate(events, start=1): #adds a counter to parameter "events" and sets start of counter to 1
        time_str = format_event_time(e)
        print(f"{i}. {time_str} - {e.get('summary', '(no title)')}")


def prompt_add_event(service):
    summary = input("Event title: ").strip()
    date_str = input("Date (YYYY-MM-DD), e.g. 2026-07-18: ").strip()
    time_str = input("Start time (HH:MM, 24-hour Dubai time), e.g. 14:30: ").strip()
    duration_str = input("Duration in minutes, e.g. 60: ").strip()

    try:
        # break down as naive datetime first (the user is typing Dubai local time)
        start_dt = datetime.datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        duration = int(duration_str)
        end_dt = start_dt + datetime.timedelta(minutes=duration)
    except ValueError:
        print("That didn't parse correctly — check the format and try again.")
        return

    # Send as plain ISO without Z — timeZone field tells Google it's Dubai time
    start_iso = start_dt.isoformat()
    end_iso = end_dt.isoformat()

    print(f"\nAbout to create: '{summary}' on {date_str} at {time_str} Dubai time ({duration} mins)")
    confirm = input("Confirm? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    new_event = add_event(service, summary, start_iso, end_iso)
    print(f"Created: {new_event.get('summary')} [id: {new_event['id']}]")


def prompt_delete_event(service):
    events = list_upcoming_events(service)
    if not events:
        print("No upcoming events to delete.")
        return

    print_events(events)
    choice = input("\nEnter the number of the event to delete (or 'c' to cancel): ").strip()
    if choice.lower() == 'c':
        print("Cancelled.")
        return

    try:
        index = int(choice) - 1
        event = events[index]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    print(f"About to delete: {event.get('summary')}")
    confirm = input("Confirm deletion? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return

    delete_event(service, event['id'])
    print("Deleted.")


def main_menu(service):
    while True:
        print("\n=== THE Calendar ===")
        print("1) List upcoming events")
        print("2) Add an event")
        print("3) Delete an event")
        print("4) Quit")
        choice = input("Choose an option: ").strip()

        if choice == '1':
            print_events(list_upcoming_events(service))
        elif choice == '2':
            prompt_add_event(service)
        elif choice == '3':
            prompt_delete_event(service)
        elif choice == '4':
            print("Goodbye!")
            break
        else:
            print("Not a valid option, try again.")


if __name__ == '__main__':
    service = get_calendar_service()
    main_menu(service)