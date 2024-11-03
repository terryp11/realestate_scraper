import random
from requests import get


class Headers():
    '''
    This class uses scrapeops api to generate and get a random header
    '''
    def __init__(self):
        scrape_ops_api_key = "ff840f76-d916-4fb0-9e07-113d68efb74c"
        response = get(
        url='https://headers.scrapeops.io/v1/browser-headers',
        params={
            'api_key': scrape_ops_api_key,
            'num_results': '200'})
        self.header_list = response.json()['result']

    def get(self):
        header = random.choice(self.header_list)
        return header
        


class Proxies():
    '''
    This class uses proxyscrape's api to generate and get a random proxy
    '''

    def __init__(self):
        url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
        p = get(url)
        self.proxy_list = p.text.split('\r\n')

    def get(self):
        proxy = random.choice(self.proxy_list)
        return proxy

