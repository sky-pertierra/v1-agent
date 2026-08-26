from calendar_tools import add_event, clear_range, delete_multiple_events, find_and_delete_event, get_calendar_service, morning_briefing, get_today_and_upcoming_events, prompt_add_event, prompt_delete_event, print_events
from docs_tools import get_docs_service, get_drive_service, create_doc, append_text, delete_doc
from brain import SYSTEM_PROMPT, interpret
import datetime
import logging

logging.basicConfig(
    filename='THE log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

def handle_action(action, calendar_service, docs_service, drive_service):
        match action:

            case {"action": "chat", "response": response}:
                print(f"V1: {response}")

            case {"action": "add_event", "summary": summary, "date": date, "time": time, "duration_mins": duration_mins}:
                start_dt = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
                end_dt = start_dt + datetime.timedelta(minutes=duration_mins)
                start_iso = start_dt.isoformat()
                end_iso = end_dt.isoformat()
                add_event(calendar_service, summary, start_iso, end_iso)
                print(f"Added: {summary} on {date} at {time}")

            case {"action": "delete_event", "search_term": search_term}:
                deleted = find_and_delete_event(calendar_service, search_term)
                if deleted:
                    print(f"Deleted event matching '{search_term}'")
                else:
                    print(f"No event found matching '{search_term}'")

            case {"action": "delete_multiple", "search_terms": search_terms}:
                deleted = delete_multiple_events(calendar_service, search_terms)
                print(f"Deleted {len(deleted)} event(s): {', '.join(deleted)}")

            case {"action": "clear_range", "start_date": start_date, "end_date": end_date}:
                clear_range(calendar_service, start_date, end_date)
                print(f"Deleted all events from {start_date} to {end_date}")
                    
            case {"action": "list_events"}:
                print_events(get_today_and_upcoming_events(calendar_service))

            case {"action": "morning_briefing"}:
                morning_briefing(calendar_service)
                
            case {"action": "create_doc", "title": title}:
                doc_id = create_doc(docs_service, title)
                print(f"Created document '{title}', with ID [id: {doc_id}]. Remember to copy!")

            case {"action": "append_text", "doc_id": doc_id, "text": text}:
                append_text(docs_service, doc_id, text)
                print(f"Added text to document with ID [id: {doc_id}].")
                
            case {"action": "delete_doc", "doc_id": doc_id}:
                delete_doc(drive_service, doc_id)
                print(f"Deleted document with ID [id: {doc_id}].")

            case {"action": "clarify", "question": question}:
                print(f"Clarification needed: {question}")

            case {"action": "unknown"}:
                print("Action unrecognized, please try again.")

def ai_menu(docs_service, drive_service, calendar_service):

    import calendar
    today = datetime.date.today()
    weekday_name = calendar.day_name[today.weekday()]
    today_str = str(today)

    conversation_history = [
        {"role": "system", "content": SYSTEM_PROMPT.format(
            today=today_str, 
            weekday=weekday_name
        )}
    ]

    while True:
        user_input = input("\nUser: ")

        if user_input.lower() in ['exit', 'quit', 'back']:
            print("Exiting AI assistant.")
            break

        conversation_history.append({"role": "user", "content": user_input})
        action, raw_response = interpret(conversation_history)
        #print(f"DEBUG: {action}")
        #print(f"DEBUG history length: {len(conversation_history)}") 
        conversation_history.append({"role": "assistant", "content": raw_response})
        if len(conversation_history) > 21:
            conversation_history = [conversation_history[0]] + conversation_history[-20:]

        if isinstance(action, list):
            for single_action in action:
                handle_action(single_action, calendar_service, docs_service, drive_service)
        else:
            handle_action(action, calendar_service, docs_service, drive_service)

# the prompt text that shows up when user requests to create doc
def prompt_create_doc(docs_service):
    name = input("Enter new doc name: ").strip()

    print(f"\nAbout to create: '{name}' in Docs.")
    confirm = input("Confirm creation? (y/n): ").strip().lower()
    if confirm == 'y':
        doc_id = create_doc(docs_service, name)
        print(f"Created document '{name}', with ID [id: {doc_id}]. Remember to copy!")
        logging.info(f"prompt_create_doc() was run and created '{name}' with ID '{doc_id}'")
    elif confirm == 'n':
        logging.info(f"prompt_create_doc() was run and cancelled the creation of '{name}'")
        return
    else:
        print("Unexpected entry!")

# the prompt text that shows up when user requests to delete doc
def prompt_delete_doc(drive_service):
    doc_id = input("Enter doc id to delete: ").strip()

    print(f"\nAbout to delete: '{doc_id}' in Docs.")
    confirm = input("Confirm deletion? (y/n): ").strip().lower()
    if confirm == 'y':
        delete_doc(drive_service, doc_id)
        print(f"Deleted document with ID [id: {doc_id}].")
        logging.info(f"prompt_delete_doc() was run and deleted the doc with ID: '{doc_id}'")
    elif confirm == 'n':
        logging.info(f"prompt_delete_doc() was run and cancelled the deletion of doc with ID: '{doc_id}'")
        return
    else:
        print("Unexpected entry!")

# the prompt text that shows up when user requests to add text to the doc
def prompt_append_text(docs_service):
    doc_id = input("Paste doc ID of doc to write into: ").strip()
    text = input("Input text to write: ")

    print(f"\nAbout to add text: '{doc_id}' in Docs.")
    confirm = input("Confirm adding text? (y/n): ").strip().lower()
    if confirm == 'y':
        append_text(docs_service, doc_id, text)
        print("awesome sauce. text added.")
        logging.info(f"prompt_append_doc() was run and added text to doc with ID: '{doc_id}'")
    elif confirm == 'n':
        logging.info(f"prompt_append_doc() was run and cancelled adding text to '{doc_id}'")
        return
    else:
        print("Unexpected entry!")

# the main menu prompt list
def main_menu(calendar_service, docs_service, drive_service):
    while True:
        print("\nTHE menu")
        print("1) Morning Briefing")
        print("2) List upcoming events")
        print("3) Add an event")
        print("4) Delete an event")
        print("5) Create document")
        print("6) Write into document")
        print("7) Delete document")
        print("ai) AI assistant")
        print("8) Quit")
        choice = input("Choose an option: ").strip()

        match choice:
            case '1':
                morning_briefing(calendar_service)
            case '2':
                print_events(get_today_and_upcoming_events(calendar_service))
            case '3':
                prompt_add_event(calendar_service)
            case '4':
                prompt_delete_event(calendar_service)
            case '5':
                prompt_create_doc(docs_service)
            case '6':
                prompt_append_text(docs_service)
            case '7':
                prompt_delete_doc(drive_service)
            case '8':
                print("Have a nice day.")
                break
            case 'ai':
                ai_menu(docs_service, drive_service, calendar_service)
            case _:
                print("Unknown prompt. Try again")

#if program file is run directly, run everything else. will not run if main.py is imported. 
if __name__ == "__main__":
    calendar_service = get_calendar_service()
    docs_service = get_docs_service()
    drive_service = get_drive_service()
    main_menu(calendar_service, docs_service, drive_service)