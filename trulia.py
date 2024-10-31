from bs4 import BeautifulSoup
from requests import RequestException, get
from json import loads
from html import unescape
from typing import Optional
from time import sleep
from random import uniform
from headers import *



def get_page(url: str, header: dict, proxy: Optional[str] = None) -> Optional[bytes]:
    sleep(uniform(0.001,3))
    try:
        response = get(url=url, headers=header, proxies={"http": proxy, "https:": proxy})
        if response.status_code == 200:
            print("REQUEST SUCCESSFUL")
            return response.content
        else:
            print(f"Failed to retrieve {url} with status code {response.status_code}")
            return None
    except RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None



def parse_page(page: bytes) -> dict:
    '''
    Uses beautifulsoup to parse the page and gets the #__NEXT_DATA__ contents
    which is basically all of the fetched data is placed in the HTML file
    in a JSON format
    '''
    soup = BeautifulSoup(page, 'lxml').select("#__NEXT_DATA__")
    if soup:
        data = loads(soup[0].getText())['props']['homeDetails']
        print("SUCCESSFULLY PARSED PAGE")
        return data
    else:
        print("UNSUCCESSFULLY PARSED PAGE")
        return None


def get_clean_data(property_data : dict) -> dict:
    '''
    Process the priceHistory dictionary
    '''
    if not property_data:
        return None

    price_history = []
    if property_data['priceHistory']:
        price_history_data = [pricehistory for pricehistory in property_data['priceHistory'] if pricehistory['event'] == 'Sold']

        for pricehistory in price_history_data:
            filtered_dic = {
                'sold_date' : pricehistory['formattedDate'],
                'price' : pricehistory['price']['formattedPrice'],
                'event' : pricehistory['event']
            }
            price_history.append(filtered_dic)

    return {
            'address' : property_data['location']['streetAddress'] if property_data['location'] else None,
            'city': property_data['location']['city'] if property_data['location'] else None,
            'zipcode': property_data['location']['zipCode'] if property_data['location'] else None,
            'state': property_data['location']['stateCode'] if property_data['location'] else None,
            'bathrooms': property_data['bathrooms']['summaryBathrooms'] if property_data['bathrooms'] else None,
            'bedrooms': property_data['bedrooms']['summaryBedrooms'] if property_data['bedrooms'] else None,
            'price': property_data['price']['price'] if property_data['price'] else None,
            'sqft': property_data['floorSpace']['formattedDimension'] if property_data['floorSpace'] else None,
            'property_type': property_data['propertyType']['value'] if property_data['propertyType'] else None,
            'price_history': price_history if price_history else None,
            'url': "https://trulia.com" + property_data['url'],
            'id': property_data['typedHomeId'],
            }