from bs4 import BeautifulSoup
from requests import get, RequestException
from json import loads
from html import unescape
from typing import Optional


def scrape_page(url : str, header : None, proxy : Optional[str] = None) -> list:
    '''
    This function grabs data of all of the properties in a url page and all of its next pages
    '''
    
    data = []
    
    response = get(url, headers = header, proxies={'http': proxy, "https:" : proxy})
    soup = BeautifulSoup(response.content,"html.parser").select("#__NEXT_DATA__")

    page = loads(soup[0].getText())['props']['pageProps']['searchPageState']['cat1']

    properties = page['searchResults']['listResults']
    data.append(properties)

    pages = [url]
    pagination = page['searchList']['pagination']

    while pagination and 'nextUrl' in pagination:
        link = 'https://www.zillow.com' + pagination['nextUrl']
        pages.append(link)
        page = get(link, headers = header, proxies={'http': proxy, "https:" : proxy})
        soup = BeautifulSoup(page.content,"html.parser").select("#__NEXT_DATA__")
        page = loads(soup[0].getText())['props']['pageProps']['searchPageState']['cat1']

        properties = page['searchResults']['listResults']
        data.append(properties)

        pagination = page['searchList']['pagination']

    data = [property for sublist in data for property in sublist]

    print(f"Total of {len(pages)} pages from {url}")
    print(f"Total of {len(data)} properties scraped")
    return data



def clean_data(property_info : dict) -> dict:
    '''
    This function cleans the data and returns a cleaned dicitionary with selected features
    '''

    house = property_info

    info = {
        "zpid": house.get('hdpData', {}).get('homeInfo', {}).get('zpid'),
        "streetaddress": house.get('addressStreet'),
        "city": house.get('addressCity'),
        "state": house.get('addressState'),
        "zipcode": house.get('addressZipcode'),
        "price": house.get('hdpData', {}).get('homeInfo', {}).get('price'),
        "sqft": house.get('hdpData', {}).get('homeInfo', {}).get('livingArea'),
        "price_per_sqft": (house.get('hdpData', {}).get('homeInfo', {}).get('price') /
                           (house.get('hdpData', {}).get('homeInfo', {}).get('livingArea'))
                           if house.get('hdpData', {}).get('homeInfo', {}).get('price') and
                           house.get('hdpData', {}).get('homeInfo', {}).get('livingArea') else None),
        "home_type": house.get('hdpData', {}).get('homeInfo', {}).get('homeType'),
        "date_sold": house.get('hdpData', {}).get('homeInfo', {}).get('dateSold'),
        "bath": house.get('hdpData', {}).get('homeInfo', {}).get('bathrooms'),
        "bed": house.get('hdpData', {}).get('homeInfo', {}).get('bedrooms'),
        "lot_area" : house.get('hdpData', {}).get('homeInfo', {}).get('livingArea'),
        "lot_area_unit": house.get('hdpData', {}).get('homeInfo', {}).get('lotAreaUnit'),
        "link": house.get('detailUrl'),
        "latitude": house.get('latLong', {}).get('latitude'),
        "longitude": house.get('latLong', {}).get('longitude'),
    }
    return info


    