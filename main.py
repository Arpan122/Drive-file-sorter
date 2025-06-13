from Google import *
from client import Client
from dotenv import load_dotenv
import pandas as pd
import os

#Scope for Google Drive API
SCOPES = ["https://www.googleapis.com/auth/drive"]

#Load gemini API key
load_dotenv()
aiAPIKey = os.getenv("GENAI_API_KEY") if os.getenv("GENAI_API_KEY") else None
assert aiAPIKey is not None, "GENAI_API_KEY environment variable is not set."

#Initialize Google Drive service and Gemini AI client
service = create_service("SensitiveStuff/credentials.json", "drive", "v3", *SCOPES)
genaiClient = Client(aiAPIKey, model="gemini-2.0-flash")

#Folder names and IDs I want to use and access
folder_names = [
    'Grade 11',
    'American History',
    'AP CSA',
    'AP Environmental Science',
    'AP Lang',
    'Biology',
    'Calc BC',
    'Spanish 2',
]
folder_ids = {
    'Grade 11': '11QVKeo6kKSJj4jMvnsMcPlkltmoQZEFC',
    'American History': '1JKt-Ys3SbtijqtdD95xLpCjOsj6xUUq6',
    'AP CSA': '1r_NfIq-0bYOjv2zsRrDL7wr8jA-Thhh3',
    'AP Environmental Science': '1wdMWmqgOUcq3kX9h1awISjjErTzBRoxI',
    'AP Lang': '1hyI1iNw4yKrqA7H6Rcub5uV3Ck_CDpb4',
    'Biology': '1704fQQHOBtSZLEbtMSPFflgMrHc0oX4P',
    'Calc BC': '1Ly03x4src5jJdGEGibYGS1Zn1_XUjs6E',
    'Spanish 2': '188oJV5EQngVfsPKNoaIOrNAwgMoran2G',
    'Sorter': '1FeqRCbmnOI7HBhCozU2kbTG297doHHYY',
}

filesInSorter = getFilesInFolder(service, folder_ids['Sorter'], extraQueries=["mimeType != 'application/vnd.google-apps.folder'"])
fileNamesInSorter = [file['name'] for file in filesInSorter]

if not filesInSorter:
    print("No files found in the Sorter folder. Exiting.")
    exit()

#print("Files in Sorter:", fileNamesInSorter)
qFolders = folder_names[1::]

genaiClient.text_prompt("Tell me which folder each file should go into based on its name. If a file does not belong in any folder, say 'None'.")

aiResponse : str | None = genaiClient.text_prompt(
    "These are the folder names: " + ", ".join(folder_names) + "\n\n" + 
    "These are the file names: " + ", ".join(fileNamesInSorter) + "\n\n" +
    "This is the output format I want it in: At the top, write 'File Sort Locations'. Then, in the immediate next line, write 'File name -> Folder name' for each file, separated by new lines. If a file does not belong in any folder, say 'File name -> None'."
)

assert aiResponse is not None, "AI response is None. Please check your API key and connection."

with open("sort_locations.txt", "w") as f:
    f.write(aiResponse.strip())

confirmation = input("Sort locations generated in sort_locations.txt. Check locations and edit if necessary.\nType 'y' if you want to proceed with move: ").strip().lower()
if confirmation != 'y':
    print("Exiting without moving files.")
    exit()

sort_locations = []
with open("sort_locations.txt", "r") as f:
    lines = f.readlines()
    for line in lines[1:]:  # Skip the first line
        file_name, folder_name = line.strip().split(" -> ")
        sort_locations.append((file_name, folder_name))

for file_name, folder_name in sort_locations:
    if folder_name == "None":
        print(f"Skipping {file_name} as it does not belong in any folder.")
        continue
    
    if folder_name not in folder_names:
        print(f"Folder '{folder_name}' does not exist. Skipping {file_name}.")
        continue
    
    folder_id = folder_ids[folder_name]
    
    file_to_move = next((file for file in filesInSorter if file['name'] == file_name), None)
    
    if file_to_move:
        service.files().update(
            fileId=file_to_move['id'],
            addParents=folder_id,
            removeParents=folder_ids['Sorter'],
            fields='id, parents'
        ).execute()
        print(f"Moved {file_name} to {folder_name}.")
    else:
        print(f"File {file_name} not found in Sorter.")