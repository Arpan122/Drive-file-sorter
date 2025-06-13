import os.path
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


def create_service(client_secret_file, api_name, api_version, *scopes):
    creds = None
    
    if os.path.exists("SensitiveStuff/token.json"):
        creds = Credentials.from_authorized_user_file("SensitiveStuff/token.json", scopes)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, scopes)
            creds = flow.run_local_server(port=0)

        with open("SensitiveStuff/token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build(api_name, api_version, credentials=creds)
        #print("Service to drive created successfully.")
        return service
    
    except Exception as error:
        print(f"An error occurred: {error}")
        
def getFilesInFolder(service, folder_id, extraQueries : list = []):
    if (len(extraQueries) > 0):
        query = f"parents = '{folder_id}' and {' and '.join(extraQueries)}"
    else:
        query = f"parents = '{folder_id}'"
    #print(f"Query: {query}")
    
    response = service.files().list(q=query).execute()
    files = response.get('files')
    page_token = response.get('nextPageToken')

    while page_token:
        response = service.files().list(q=query, next_page_token=page_token).execute()
        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken')

    return files