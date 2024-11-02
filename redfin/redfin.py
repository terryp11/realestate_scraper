from requests import get
from bs4 import BeautifulSoup



def scrape_redfin(url):

    redfin = get('https://www.redfin.com/CA/Pomona/1708-Palmgrove-Ave-91767/home/7890597')
    x = BeautifulSoup(redfin.content, 'html.parser')

    print(x.select('div[class="statsValue"]')[0].getText())
    print(x.select('div[class="street-address"]')[0].getText())
    print(x.select('div[data-rf-test-id="abp-cityStateZip"]')[0].getText())
    print(x.select('div[class="statsValue"]')[1].getText()) # beds
    print(x.select('div[class="statsValue"]')[2].getText()) # bath
    print(x.select('span[class="statsValue"]')[0].getText()) # sqft

    