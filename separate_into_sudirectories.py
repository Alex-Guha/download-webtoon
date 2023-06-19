import os
import shutil

def organize_files(directory):
    # Get a list of files in the directory
    files = os.listdir(directory)

    # Create a dictionary to store the files by their base name
    file_dict = {}

    # Iterate over each file
    for filename in files:
        # Get the base name without the extension
        base_name = os.path.splitext(filename)[0]

        # Add the file to the dictionary
        if base_name in file_dict:
            file_dict[base_name].append(filename)
        else:
            file_dict[base_name] = [filename]

    # Iterate over the files in the dictionary
    for base_name, filenames in file_dict.items():
        # Create the subdirectory if it doesn't exist
        subdirectory_path = os.path.join(directory, "4_image_"+(base_name.zfill(3)))
        os.makedirs(subdirectory_path, exist_ok=True)

        # Move each file into the subdirectory
        for filename in filenames:
            file_path = os.path.join(directory, filename)
            shutil.move(file_path, subdirectory_path)

            print(f"Moved '{filename}' to '{base_name}' subdirectory.")

def move_files_to_main_directory(main_directory):
    # Get a list of all subdirectories
    subdirectories = [subdir for subdir in os.listdir(main_directory) if os.path.isdir(os.path.join(main_directory, subdir))]

    # Move files from each subdirectory to the main directory
    for subdir in subdirectories:
        subdir_path = os.path.join(main_directory, subdir)
        files = os.listdir(subdir_path)
        for file_name in files:
            file_path = os.path.join(subdir_path, file_name)
            destination_path = os.path.join(main_directory, file_name)
            shutil.move(file_path, destination_path)
        # Remove the now empty subdirectory
        os.rmdir(subdir_path)

# Specify the directory where the files are located
directory_path = "Blue_Matter_tailored"

organize_files(directory_path)
#move_files_to_main_directory(directory_path)