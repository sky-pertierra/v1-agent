from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os
SCOPES = ['https://www.googleapis.com/auth/calendar','https://www.googleapis.com/auth/documents','https://www.googleapis.com/auth/drive']

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

def get_docs_service():  
    return build('docs', 'v1', credentials=get_credentials())       

def get_drive_service():
      return build('drive', 'v3', credentials=get_credentials())

def create_doc(docs_service, title):
      response = docs_service.documents().create(body={'title': title}).execute()
      return response.get('documentId', None)

# adds text to the document using doc ID and inputted text
def append_text(docs_service, doc_id, text):
    doc = docs_service.documents().get(documentId=doc_id).execute()
    end_index = doc['body']['content'][-1]['endIndex'] - 1
    requests = [
        {
        'insertText': {
            'location': {'index': end_index,},
            'text': text + ' '
        }
        }
    ]
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={'requests': requests}
    ).execute()

def delete_doc(drive_service, doc_id):
      drive_service.files().delete(fileId=doc_id).execute()

if __name__ == '__main__':
    docs_service = get_docs_service()
    drive_service = get_drive_service()

    print("Creating doc...")
    doc_id = create_doc(docs_service, "THE test file")
    print(f"Created with ID: {doc_id}")

    print("Adding text...")
    append_text(docs_service, doc_id, "wsg stingalings.")
    print("Text added.")

    #print("Deleting doc...")
    #delete_doc(drive_service, doc_id)
    #print("Deleted.")###
    