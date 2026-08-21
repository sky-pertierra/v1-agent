#imports the shi
from calendar_tools import get_calendar_service, morning_briefing, get_upcoming_events, prompt_add_event, prompt_delete_event, print_events
from docs_tools import get_docs_service, get_drive_service, create_doc, append_text, delete_doc
import logging

logging.basicConfig(
    filename='THE log.txt',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

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
        print("8) Quit")
        choice = input("Choose an option: ").strip()

        match choice:
            case '1':
                morning_briefing(calendar_service)
            case '2':
                print_events(get_upcoming_events(calendar_service))
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
            case _:
                print("Unknown prompt. Try again")

#if program file is run directly, run everything else. will not run if main.py is imported. 
if __name__ == "__main__":
    calendar_service = get_calendar_service()
    docs_service = get_docs_service()
    drive_service = get_drive_service()
    main_menu(calendar_service, docs_service, drive_service)