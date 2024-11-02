from bs4 import BeautifulSoup
from requests import get
from json import loads
from html import unescape
from headers import *
from typing import Optional




def get_house_links(page_url : str, header : dict, proxy : Optional[str] = None):
    '''
    This function returns a list of urls of all the properties on a page
    '''
    response = get(url = page_url, headers = header, proxies = {'http' : proxy,'https:' : proxy})

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'lxml').select("#__NEXT_DATA__")
        if soup:
            properties_data = loads(soup[0].getText())['props']['searchData']['homes']

            links = ["https://trulia.com" + property['url'] for property in properties_data]
            print(f"{len(links)} property links scraped from {page_url}")
            return links
        else:
            print("Error scraping page")
            return None
    else:
        return response.raise_for_status()
    


def get_page_urls(url, header: dict, proxy: Optional[str] = None):
    '''
    This function grabs all of pages of house listings in a given area
    '''
    page = get(url, headers = header, proxies = {'http' : proxy,'https:' : proxy})
    next_page = BeautifulSoup(page.content, "lxml").find_all("li", {"data-testid" : "pagination-next-page"})
    pages = [url]

    while next_page:
        sublink = next_page[0].find('a')['href']
        link = 'https://www.trulia.com' + sublink
        pages.append(link)
        page = get(link, headers = header, proxies = {'http' : proxy,'https:' : proxy})
        next_page = BeautifulSoup(page.content, "lxml").find_all("li", {"data-testid" : "pagination-next-page"})

    print(f"Total of {len(pages)} pages from {url}")
    return pages