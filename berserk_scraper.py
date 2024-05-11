import os
import requests
import PyPDF2
import img2pdf
import pdb
import pprint
import sys
from bs4 import BeautifulSoup
from urllib.parse import urlparse

chapters_with_missing_pages = {}

def scrape(url, img_dir, chapter_name_slug):
    """ Sends a GET Request to the url provided and downloads every image displayed on the page.

    url -> str: the url of the webpage we want to download every image from. probably an individual chapter of a manga
    img_dir -> str: the path of where you want the images stored. this is dynamically made in the main() function

    """

    # Send a GET request to the webpage, and then parse the HTML content
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all the images
    main_div = soup.find('div', class_='pages') #!WILL NEED TO BE UPDATED BASED ON WEBSITE
    img_tags = main_div.find_all('div', class_='img_container')

    # Create a directory to store downloaded images
    if not os.path.exists(img_dir):
        os.makedirs(img_dir)

    total_page_count = len(img_tags)
    page_count = 0

    download_with_loading_bar(page_count, total_page_count)

    # Loop through all <img> tags and download images
    for img_tag in img_tags: 
        image = img_tag.find('img', class_='pages__img') #!MIGHT NEED TO BE UPDATED BASED ON WEBSITE
        img_url = image['src']

        if "?t=" in img_url:
            index = img_url.find('?t=')
            img_url = img_url[:index]

        if img_url.endswith('\r'):
            img_url = img_url.rstrip('\r')

        if img_url.endswith(".jpg") or img_url.endswith(".jpeg"):
            pass
        else:
            chapters_with_missing_pages[img_url] = (chapter_name_slug)
            continue

        image_name = f"{chapter_name_slug}-page-{page_count}"
        img_extension = os.path.splitext(urlparse(img_url).path)[-1] #make sure the image is still a jpeg
        img_path = os.path.join(img_dir, image_name + img_extension) #actually download the file
        
        # Download image content
        img_response = requests.get(img_url)
        
        # Save image content to file
        with open(img_path, 'wb') as img_file:
            img_file.write(img_response.content)
            
        page_count += 1
        download_with_loading_bar(page_count, total_page_count)

    print()
    print("===============================================")
    print("All images downloaded successfully.")

def download_with_loading_bar(progress, total_size):
    """ Displays a loading bar based on the progress of a download (scrape)

    progress -> int: current total progress out of total size
    total_size -> int: the number of things we are downloading
    
    """

    # Set the length of the bar
    bar_length = 50

    # Calculate percentage completion
    percent = progress / total_size
    completed = int(bar_length * percent)
    remaining = bar_length - completed

    # Print the loading bar
    sys.stdout.write("\r[" + "#" * completed + "-" * remaining + f"] {percent:.2%}")
    sys.stdout.flush()

def images_to_pdf(directory, output_name):
    """Takes a collection of images stored in a folder and turns them into a PDF

    directory -> str: Location where you would like the final pdf to be stored
    output_name -> str: Name of PDF
    
    """

    # List all files in the directory and filter only JPEG images (ending with ".jpg")
    image_files = [i for i in os.listdir(directory)]

    # Sort the image files based on page number:
    image_files = sorted(image_files, key=lambda x: int(x.split('-')[-1].split('.')[0]))

    # Initialize a list to store image data
    image_data = []

    # Read each image file and add its data to the list
    for image_file in image_files:
        with open(os.path.join(directory, image_file), "rb") as f:
            image_data.append(f.read())

    # Convert the list of image data to a single PDF file
    pdf_data = img2pdf.convert(image_data)

    # Write the PDF content to a file
    with open(output_name, "wb") as file:
        file.write(pdf_data)

    print("...PDF GENERATED")

def reverse_pdf(input_pdf, output_pdf):
    """ Reverses a pdf

    input_pdf -> str: Location (path) of the pdf we are reversing
    output_pdf -> str: Location (path) of the reversed pdf
    
    """

    # Open the input PDF file
    with open(input_pdf, 'rb') as file:
        reader = PyPDF2.PdfReader(file)
        writer = PyPDF2.PdfWriter()

        # Reverse the order of pages
        for page_num in range(len(reader.pages) - 1, -1, -1):
            writer.add_page(reader.pages[page_num])

        # Write the reversed PDF to the output file
        with open(output_pdf, 'wb') as output_file:
            writer.write(output_file)
    
    print("...PDF REVERSED")

def get_chapter_links(url):
    """ Creates a list of all of the chapters in the specified manga

    url -> str: URl of the homepage of the website
    
    """

    # Send a GET request to the webpage, and then parse the HTML content
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    chapters = soup.find_all("a", class_="btn btn-sm btn-primary mr-2")

    return list(chapters)

def chapter_name(url, distinguisher):
    """ Creates slugified names based on url

    i.e
    url = https://readberserk.com/chapter/berserk-chapter-a0/ 
    returns: berserk-chapter-a0

    url -> str: URL of chapter we are processing
    distinguisher -> str: where you want to start the name (chapter/ in the above ex) 
        
    """
    start_index = url.find(distinguisher)

    if start_index != -1:
        start_index += len(distinguisher)
        end_index = url.find("/", start_index)

        if end_index != -1:
            return url[start_index:end_index]
        
    return None

def main():
    #get all of the links to each chapter
    links = get_chapter_links('https://readberserk.com/')

    for link in links:
        url = link["href"]
        chapter_name_slug = chapter_name(url, "chapter/")
        img_dir = f'../NO-PNG-CONTENT/IMAGES/{chapter_name_slug}'
        input_name = f'../NO-PNG-CONTENT/PDFS/{chapter_name_slug}.pdf'
        output_name = f'../NO-PNG-CONTENT/REV_PDFS/{chapter_name_slug}-reversed.pdf'

        print(f"CURRENTLY PROCESSING {chapter_name_slug}")
        print("===============================================")

        # gather all the images from the specified URL, and download them to the path provided in img_dir
        scrape(url, img_dir, chapter_name_slug)

        # turn those images into a pdf
        images_to_pdf(img_dir, input_name)

        # reverse the pdf so it's readable in manga format
        reverse_pdf(input_name, output_name)

        print("===============================================\n\n\n")
    
    print("ALL CHAPTERS DOWNLOADED! PLEASE NOT THESE CHAPTERS HAD SOME ERRORS AND SKIPPED SOME PAGES ON THE WEBSITE. PLEASE DOUBLE CHECK THESE CHAPTERS BEFORE READING")
    print(pprint.pprint(chapters_with_missing_pages))

if __name__ == '__main__':
    main()