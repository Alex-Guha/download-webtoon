import os
from PIL import Image

directory = 'temp'  # Replace with the path to your image directory

def get_aspect_ratio(image_path):
    with Image.open(image_path) as img:
        width, height = img.size
        aspect_ratio = width / height
        return aspect_ratio, width, height

def count_same_ratios(image_directory):
    aspect_ratios = []
    dims = []
    for filename in os.listdir(image_directory):
        if filename.endswith(('.png', '.jpg', '.jpeg')):
            file_path = os.path.join(image_directory, filename)
            aspect_ratio, width, height = get_aspect_ratio(file_path)
            aspect_ratios.append(aspect_ratio)
            dims.append(width)
            dims.append(height)

    num_same_ratios = len(aspect_ratios) - len(set(aspect_ratios))
    print(f"Min dim: {min(dims)}, max dim: {max(dims)}")

    return num_same_ratios

# Call the function to count the number of images with the same aspect ratio in the specified directory
same_ratio_count = count_same_ratios(directory)
print(f"The number of images with the same aspect ratio: {same_ratio_count}")
