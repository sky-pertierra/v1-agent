from asyncio import events

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
import datetime
import logging

SCOPES = ['https://www.googleapis.com/auth/calendar','https://www.googleapis.com/auth/documents','https://www.googleapis.com/auth/drive']

# Your local timezone offset — Dubai is UTC+4
# Change this if you move timezone
LOCAL_UTC_OFFSET = 4


def utc_now():
    """Returns current UTC time as a timezone-aware datetime."""
    return datetime.datetime.now(datetime.timezone.utc)


def local_now():
    """Returns current local time (Dubai, UTC+4)."""
    offset = datetime.timezone(datetime.timedelta(hours=LOCAL_UTC_OFFSET))
    return datetime.datetime.now(offset)

# gets credentials. what did you expect lol
def get_credentials(): 
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

# uses the credentials to create the resource to interact with Google Calendar API
def get_calendar_service():
    return build('calendar', 'v3', credentials=get_credentials())

def get_today_and_upcoming_events(service, max_results=10):
    """Get all upcoming events from today onwards."""
    local = local_now()
    start_of_day = local.replace(hour=0, minute=0, second=0, microsecond=0)
    result = service.events().list(
        calendarId='primary',
        timeMin=start_of_day.isoformat(),
        maxResults=max_results,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return result.get('items', [])


def get_events_today(service):
    """Get all events happening today in local time."""
    local = local_now()
    start_of_day = local.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = local.replace(hour=23, minute=59, second=59, microsecond=0)
    result = service.events().list(
        calendarId='primary',
        timeMin=start_of_day.isoformat(),
        timeMax=end_of_day.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return result.get('items', [])


def get_events_in_next_hours(service, hours=3):
    """Get events happening within the next N hours."""
    now = utc_now()
    future = now + datetime.timedelta(hours=hours)
    result = service.events().list(
        calendarId='primary',
        timeMin=now.isoformat(),
        timeMax=future.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    return result.get('items', [])

# no idea why this is here
def add_event(service, summary, start_iso, end_iso):
    """Add a new calendar event."""
    event = {
        'summary': summary,
        'start': {'dateTime': start_iso, 'timeZone': 'Asia/Dubai'},
        'end': {'dateTime': end_iso, 'timeZone': 'Asia/Dubai'},
    }
    return service.events().insert(calendarId='primary', body=event).execute()

# also no idea
def delete_event(service, event_id):
    """Delete a calendar event by ID."""
    service.events().delete(calendarId='primary', eventId=event_id).execute()

def find_and_delete_event(service, search_term):
    events = get_today_and_upcoming_events(service)
    for event in events:
        if search_term.lower() in event.get('summary', '').lower():
            delete_event(service, event['id'])
            return True
    return False

def print_events(events):
    if not events:
        print("No upcoming events found.")
        logging.info("print_events() was run and found no events.")
        return
    for i, e in enumerate(events, start=1): #adds a counter to parameter "events" and sets start of counter to 1
        time_str = format_event_time(e)
        print(f"{i}. {time_str} - {e.get('summary', '(no title)')}")
    logging.info("print_events() was run and outputted events.")

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
    if confirm == 'y':
        new_event = add_event(service, summary, start_iso, end_iso)
        print(f"Created: {new_event.get('summary')} [id: {new_event['id']}]")
        logging.info(f"prompt_add_event() was run and added the event: {summary} on {date_str}")
    elif confirm == 'n':
        logging.info(f"prompt_add_event() was run and cancelled the addition of event: {summary}")
        return
    else:
        print("Unexpected entry!")


def prompt_delete_event(service):
    events = get_today_and_upcoming_events(service)
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
    if confirm == 'y':
        delete_event(service, event['id'])
        print(f"Deleted event: {event.get('summary')}.")
        logging.info(f"prompt_delete_event() was run and deleted the event: {event.get('summary')}")
    elif confirm == 'n':
        logging.info(f"prompt_delete_event() was run and cancelled the deletion of event: {event.get('summary')}")
        return
    else:
        print("Unexpected entry!")

def delete_multiple_events(service, search_terms): 
    """Delete multiple events based on a list of search terms."""
    deleted_events = []
    for term in search_terms:
        if find_and_delete_event(service, term):
            deleted_events.append(term)
    return deleted_events

def clear_range(service, start_date, end_date):
    """Delete all events in a specified date range."""
    dubai_offset = datetime.timezone(datetime.timedelta(hours=4))

    start_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d").replace(tzinfo=dubai_offset)
    end_dt = (datetime.datetime.strptime(end_date, "%Y-%m-%d") + 
    datetime.timedelta(days=1)).replace(tzinfo=dubai_offset)
    events = service.events().list(
        calendarId='primary',
        timeMin=start_dt.isoformat(),
        timeMax=end_dt.isoformat(),
        singleEvents=True,
        orderBy='startTime'
    ).execute().get('items', [])

    if not events:
        print("No events found in that range.")
        return

    print(f"Found {len(events)} event(s) to delete between {start_date} and {end_date}:")
    for e in events:
        print(f"  - {e.get('summary', '(no title)')}")

    confirm = input("Delete all events? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    elif confirm == 'y':
        print("Deleting events...")

    for event in events:
        delete_event(service, event['id'])


def format_event_time(event):
    """Return a readable local time string for an event."""
    start_str = event['start'].get('dateTime', event['start'].get('date'))
    try:
        dt = datetime.datetime.fromisoformat(start_str)
        # Convert to local time
        offset = datetime.timezone(datetime.timedelta(hours=LOCAL_UTC_OFFSET))
        dt_local = dt.astimezone(offset)
        return dt_local.strftime('%I:%M %p')
    except Exception:
        return start_str


def morning_briefing(service):
    """Print a clean summary of today's events."""
    now = local_now()
    print(f"\n Good morning. Today is {now.strftime('%A, %B %d %Y')}.")
    print("-" * 40)

    events = get_events_today(service)

    if not events:
        print(" You have no events scheduled today.")
        logging.info("morning_briefing() was run and found no events.")
    else:
        print(f" You have {len(events)} event(s) today:\n")
        for e in events:
            time_str = format_event_time(e)
            title = e.get('summary', '(no title)')
            print(f"   {time_str} — {title}")
        logging.info(f"morning_briefing() was run and found {len(events)} events.")

    # Warn about anything in the next 3 hours
    upcoming = get_events_in_next_hours(service, hours=3)
    if upcoming:
        print(f"\n Coming up in the next 3 hours:")
        for e in upcoming:
            time_str = format_event_time(e)
            title = e.get('summary', '(no title)')
            print(f"   ⚡ {time_str} — {title}")
        logging.info("morning_briefing() was run and found upcoming events in the next 3 hours.")

    print("-" * 40)


if __name__ == '__main__':
    service = get_calendar_service()
    morning_briefing(service)