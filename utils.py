from PyPDF2 import PdfFileReader
import os
import requests
from pathlib import Path
from tika import parser
import urllib.request

DOWNLOADS_PATH = os.path.join(os.getcwd(), 'downloads')


def download_file(title, link):
    r = requests.get(link, headers={'Authorization': 'Bearer %s' % os.environ["SLACK_BOT_TOKEN"]})
    download_path = os.path.join(DOWNLOADS_PATH, title)
    # print(download_path)
    # filename = Path(download_path)
    # response = requests.get(link)
    # filename.write_bytes(response.content)
    # urllib.request.urlretrieve(link, download_path)
    print(f"Status = {r.raise_for_status}")
    file_data = r.content   # get binary content
    # save file to disk
    with open(download_path , 'w+b') as f:
        f.write(bytearray(file_data))


def read_pdf(filename):
    # creating an object
    file_path = os.path.join(DOWNLOADS_PATH, filename) 
    text = parser.from_file(file_path)
    return text['content']
    # print(raw['content'])