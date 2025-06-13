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
print("Gemini service initialized successfully.")
genaiClient = Client(aiAPIKey, model="gemini-2.0-flash")
print("Google Drive service initialized successfully.\n")

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
    'Sorter': '1rWLlSKDuqbCRyEAR-Kn7Uv06u154OSYh',
    'Trash': '1EBHYk0mMMzj1P62OFAaJqcK0YNlDYLit'
}

fileList = getFilesInFolder(service, folder_ids['Sorter'], extraQueries=["mimeType != 'application/vnd.google-apps.folder'"])
fileIds = [file['id'] for file in fileList]
filesInSorter = []
for fileId in fileIds:
    file = service.files().get(fileId=fileId, fields='name, modifiedTime, id').execute()
    filesInSorter.append((file['name'], file['modifiedTime'].split("T")[0], file['id']))

if filesInSorter:
    print("Files in Sorter folder:")
    for file_name, modified_time, id in filesInSorter:
        print(f"File: {file_name}, Last Modified: {modified_time}")
    print()
else:
    print("No files found in the Sorter folder. Exiting.")
    exit()

qFolders = folder_names[1::]

#Setting up
genaiClient.text_prompt(f"Tell me which folder each file should go into based on its name and last modified time. If a file has not been modified in the last 3 months (today's date is {datetime.date.today()}), move it to a folder called 'Trash'. If you can't figure out where a file should go, say 'None'.")

fileInfoPrompt = "These are the file names and the last time they were modified:"
for file_name, modified_time, id in filesInSorter:
    fileInfoPrompt += f" {file_name}, {modified_time};"
aiResponse : str | None = genaiClient.text_prompt(
    "These are the folder names: " + ", ".join(folder_names) + "\n\n" + 
    fileInfoPrompt + "\n\n" +
    f"This is the output format I want it in: At the top, write 'File Sort Locations'. Then, in the immediate next line, write 'File name -> Folder name' for each file, separated by new lines. If a file has not been modified in the last 3 months (today's date is {datetime.date.today()}), say 'File name -> Trash'. Prioritize dates over name when categorizing. If a file does not belong in any folder, say 'File name -> None'."
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
    elif folder_name == "Trash":
        c = input(f"Trashing {file_name}. Continue? (y/n): ").strip().lower()
        if c != 'y':
            print(f"Skipping {file_name}.")
            continue
    
    if folder_name not in folder_names:
        print(f"Folder '{folder_name}' does not exist. Skipping {file_name}.")
        continue
    
    folder_id = folder_ids[folder_name]
    
    file_to_move = next((file for file in filesInSorter if file[0] == file_name), None)
    
    if file_to_move:
        service.files().update(
            fileId=file_to_move[2],
            addParents=folder_id,
            removeParents=folder_ids['Sorter'],
            fields='id, parents'
        ).execute()
        print(f"Moved {file_name} to {folder_name}.")
    else:
        print(f"File {file_name} not found in Sorter.")
        
print("All files processed. Ending.")