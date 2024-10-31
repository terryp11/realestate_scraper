from bs4 import BeautifulSoup
from requests import get
from json import loads
from html import unescape



def get_house_links(area_url : str, header : dict[str:str], proxy : None):

    response = get(url = area_url, headers = header, proxies = {'http' : proxy,'https:' : proxy})

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser').select("#__NEXT_DATA__")
        properties_data = loads(soup[0].getText())['props']['pageProps']

        links = [property['detailUrl'] for property in properties_data['searchPageState']['cat1']['searchResults']['listResults']]
        return links
    else:
        return response.raise_for_status()
    



def get_next_page_url(url : str, header : None, proxy : None):

    response = get(url, headers = header, proxies={
        'http': proxy,
        "https:" : proxy})
    
    json = loads(BeautifulSoup(response.content,"html.parser").select("#__NEXT_DATA__")[0].getText())
    pagination = json['props']['pageProps']['searchPageState']['cat1']['searchList']['pagination']

    if 'nextUrl' in pagination:
        return 'https://www.zillow.com' + pagination['nextUrl']
    else:
        return None