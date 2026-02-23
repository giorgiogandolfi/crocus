import glob
import json
import os
import requests

# TODO: implement logging


def create_folder(folder_path: str) -> None:
    """
    Create a folder if it does not exist
    """
    if not os.path.exists(folder_path):
        os.makedirs(folder_path, exist_ok=True)


def write_json(file_path: str, content: dict) -> None:
    """
    Write into a JSON file
    """
    directory = os.path.dirname(file_path)

    # Ensure the directory exists
    os.makedirs(directory, exist_ok=True)
    with open(file_path, "w") as json_file:
        json.dump(content, json_file, indent=4)


def read_json(file_path: str) -> dict:
    """
    Read a JSON file
    """
    with open(file_path, "r") as file:
        data = json.load(file)
        return data


def rename_latest_file_in_folder(base_path: str, full_path: str, new_name: str) -> bool:
    """
    Renames the most recently created or modified file in the base_path.
    Saves the renamed file in the full_path
    """
    files = [f for f in glob.glob(os.path.join(base_path, "*")) if os.path.isfile(f)]
    if not files:
        return False

    latest_file = max(files, key=os.path.getmtime)
    file_extension = latest_file.split(".")[-1]
    new_name = ".".join([new_name, file_extension])
    # Create the full path for the new file
    new_file_path = os.path.join(full_path, new_name)
    try:
        os.rename(latest_file, new_file_path)
        return True
    except Exception as e:
        print(e)
        return False


def download_file_with_request(url: str, folder: str, file_name: str) -> None:
    """
    Download a file from a URL using requests
    """
    response = requests.get(url)
    if response.status_code == 200:
        file_path = os.path.join(folder, file_name)
        with open(file_path, "wb") as file:
            file.write(response.content)
    else:
        print(f"Failed to download file: {response.status_code}")
