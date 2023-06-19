import requests, os, re, urllib.parse
from bs4 import BeautifulSoup
from PIL import Image

def is_valid_filename(filename):
    pattern = r'^[^<>:"/\\|?*\x00-\x1F]*$'  # Regular expression pattern for valid filenames
    return re.match(pattern, filename) is not None

def make_valid_filename(filename):
    return re.sub(r'[<>:"/\\|?*\x00-\x1F]', '_', filename)

def download_image(url, directory, ep, page_num, referer):
    # Extract the image file name from the URL
    real_filename = url.split("/")[-1]
    
    response = requests.get(url, headers={"Referer": referer})

    used_filename = str(page_num).zfill(3) + "_" + str(ep).zfill(4) + ".png"
    with open(os.path.join(directory, used_filename), "wb") as f:
        f.write(response.content)
    print(f"[download_image]\tImage downloaded: {real_filename.split('?')[0]} as {used_filename}")
    response.close()

def crawl_images(url, directory, page_num, referer):
    print(f"[crawl_images]\t\tSending a GET request to the URL {url}")
    response = requests.get(url, headers={"Referer": referer})

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all the "img" tags in the HTML
    img_tags = soup.find_all("img", class_="_images")

    response.close()
    
    # Download images
    for ep, img in enumerate(img_tags):
        img_url = img.get("data-url")
        if img_url.startswith("http"):
            download_image(img_url, directory, ep+1, page_num, url)

def fetch_links(url, class_names):
    print(f"[fetch_links]\t\tSending a GET request to the URL {url}")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    # Find all elements with the specified class names
    elements = soup.find_all(class_=class_names[0])
    
    # Filter elements based on sequential class names
    for class_name in class_names[1:]:
        element = soup.find(class_=class_name)
        if element is not None:
            elements.append(element)
    
    # Extract the links from the elements
    links = [element['href'] for element in elements if 'href' in element.attrs]
    
    return links

def recursive_webpage_count(url, soup, i):
    if soup.find('div', class_="paginate").find_all("a")[-1].find("span") is None:
        i += 10
        response = requests.get(url + "&page=" + str(i+1))
        soup = BeautifulSoup(response.text, 'html.parser')
        return recursive_webpage_count(url, soup, i)
    else:
        return int(soup.find('div', class_="paginate").find_all("a")[-1].find("span").text)

def fetch(url):
    title_number = url.split("=")[-1]
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    response.close()
    if soup.find('div', class_="info") is None:
        webtoon_name = soup.find('h3', class_="subj _challengeTitle").text.strip()
    else:
        webtoon_name = soup.find('h1', class_="subj").text.strip()
    number_of_episodes = int(soup.find('ul', id="_listUl").find('li')["data-episode-no"])

    directory = ""
    if not is_valid_filename(webtoon_name):
        directory = make_valid_filename(webtoon_name)
    else:
        directory = webtoon_name

    directory = directory + "/" + directory + " Panels/" + directory

    num_existing = 0
    # Create the directory if it doesn't exist
    if os.path.exists(directory):
        # Compare number of eps to what we already have downloaded
        if os.path.exists(directory + "_stitched"):
            num_existing = len(os.listdir(directory + "_stitched/"))
            if num_existing == number_of_episodes:
                print("[fetch]\t\t\tAlready up to date")
                return directory, number_of_episodes
            else:
                print(f"[fetch]\t\t\t{num_existing} episodes found in {directory}_stitched, exluding them from episodes to download")
    else:
        # Make the directory since it doesn't exist
        os.makedirs(directory)
    

    number_of_webpages = recursive_webpage_count(url, soup, 0)
    webpage_urls = []
    for i in range(number_of_webpages):
        webpage_urls.append(url + "&page=" + str(i+1))
    class_names = []
    for i in range(num_existing, number_of_episodes):
        class_names.append("NPI=a:list,i=" + str(title_number) + ",r=" + str(i+1) + ",g:en_en")

    webpage_urls.reverse()
    i = 1 + num_existing
    for webpage_url in webpage_urls:
        links = fetch_links(webpage_url, class_names)
        for link in links:
            crawl_images(link, directory, i, webpage_url)
            i += 1

    return directory, number_of_episodes

def fetch_by_name(webtoon_name, canvas=False):
    encoded_string = urllib.parse.quote(webtoon_name)
    base_search_url = "https://www.webtoons.com/en/search?keyword=" + encoded_string
    print(f"[fetch_by_name]\t\tQuerying webtoon search for \"{webtoon_name}\" as URL {base_search_url}")
    response = requests.get(base_search_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    response.close()

    try:
        if not canvas:
            url = "https://www.webtoons.com" + soup.find('ul', class_="card_lst").find('li').find('a')['href']
        else:
            url = "https://www.webtoons.com" + soup.find('div', class_="challenge_lst search").find('ul').find('li').find('a')['href']
    except AttributeError:
        print(f"[-]\t\t\t\t\tSearch returned no results for {webtoon_name}")
        return
    print(f"[fetch_by_name]\t\tFetching the first search result")
    response = requests.get(url, allow_redirects=False)
    url = "https://www.webtoons.com" + response.headers['Location']
    response.close()
    return fetch(url)

def stitch_images_vertically(directory, i):
    image_files = [f for f in os.listdir(directory) if (os.path.isfile(os.path.join(directory, f)) and f.split('_')[0] == i)]
    image_files.sort()  # Sort the files in alphabetical order

    images = [Image.open(os.path.join(directory, img)) for img in image_files]
    widths, heights = zip(*(img.size for img in images))

    total_width = max(widths)
    total_height = sum(heights)

    stitched_image = Image.new('RGB', (total_width, total_height))

    y_offset = 0
    for img in images:
        stitched_image.paste(img, (0, y_offset))
        y_offset += img.size[1]

    output_path = directory + "_stitched/" + i + ".png"
    stitched_image.save(output_path)
    print(f"[stitch]\t\tStitched image saved as {output_path}")


def stitch(directory, number_of_episodes):
    num_existing = 0
    if os.path.exists(directory + "_stitched/"):
        #get num of existing files and remove them from the range
        num_existing = len(os.listdir(directory + "_stitched/"))
    else:
        os.makedirs(directory + "_stitched/")

    if num_existing == number_of_episodes:
        print("[stitch]\t\tAlready up to date")
        return

    for i in range(num_existing, number_of_episodes):
        stitch_images_vertically(directory, str(i+1).zfill(3))


if __name__ == "__main__":
    print("Note: This will only work on Webtoon comic\nThis will not work on daily pass comics")
    if not int(input("Enter \"0\" for lookup by name or \"1\" for lookup by url: ")):
        webtoon_name = input("Input the name of the webtoon: ")
        canvas = int(input("Is this a canvas title? \"1\" for yes, \"0\" for no: "))
        stitch(*fetch_by_name(webtoon_name, canvas))
    else:
        url = input("Paste the webtoon's url: ")
        stitch(*fetch(url))