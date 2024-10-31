from bs4 import BeautifulSoup
from requests import get, RequestException
from json import loads
from html import unescape
from typing import Optional



def get_page(url: str, headers: dict[str, str], proxies: Optional[str] = None) -> Optional[bytes]:
    try:
        response = get(url=url, headers=headers, proxies={"http": proxies, "https": proxies})
        if response.status_code == 200:
            print("SUCCESS")
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
    soup = BeautifulSoup(page, 'html.parser').select("#__NEXT_DATA__")
    data = loads(loads(unescape(soup[0].getText()))['props']['pageProps']['componentProps']['gdpClientCache'])
    for value in data.values():
        if "property" in value:
            parsed_property_data = value.get("property")

    return parsed_property_data


def get_clean_data(property_data : dict) -> dict:

    keys_to_keep = ['date', 'price', 'pricePerSquareFoot']
    x = [action for action in property_data['priceHistory'] if action['event'] == 'Sold']
    price_history = []
    for dic in x:
        filtered_dic = {key: dic[key] for key in keys_to_keep if key in dic}
        price_history.append(filtered_dic)

    return {
            'zpid' : property_data['zpid'],
            'address' : property_data['streetAddress'],
            'city' : property_data['city'],
            'state' : property_data['state'],
            'zipcode' : property_data['zipcode'],
            'price' : property_data['price'],
            'yearBuilt' : property_data['yearBuilt'],
            'bedrooms' : property_data['bedrooms'],
            'bathrooms' : property_data['bathrooms'],
            'priceHistory' : price_history
            }