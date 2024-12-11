from zillow.zillow import *
from bs4 import BeautifulSoup
from requests import get
from headers import *


def get_zipcodes(county_name: str, state: str) -> list:
    '''
    Gets the zipcodes from a county through the zillow website

    Args:
        county_name (str): county name
        state (str): US state 2 letter abbreviation
    '''

    header = Headers().get()
    name = county_name.replace(" ", "-")
    request = get(f"https://www.zillow.com/browse/homes/{state}/{name}/", headers=header)

    zipcodes = [a.text for a in BeautifulSoup(request.content, 'html.parser').select(
        "section[class = 'bh-content-component']")[0].find_all('a')]

    # Checking to see if the list contains all zipcodes (numeric values)
    if all(zipcode.isdigit() for zipcode in zipcodes):
        return zipcodes
    else:
        raise ValueError("Invalid data encountered: some zip codes are not numeric. Check if the right county name was entered.")


def zillowzip_runner(db, county_name, state):
    z = ZillowScraper()
    z.set_db(db)
    for zipcode in get_zipcodes(county_name, state):
        z.scrape_zipcode_to_db(zipcode)

    print(f"** Scraped a total of {z.total_properties} scraped from {county_name}, {state}")


def main():
    '''
    Run to scrape orange county, los angeles, and san bernardino zipcodes
    '''

    # Los Angeles
    print("***** STARTING LOS ANGELES COUNTY *****")
    zillowzip_runner("zillow_data.db", "los angeles county", "ca")
    print("***** FINISH SCRAPING LOS ANGELES COUNTY *****")

    # Orange County
    print("***** STARTING ORANGE COUNTY *****")
    zillowzip_runner("zillow_data.db", "orange county", "ca")
    print("***** FINISH SCRAPING ORANGE COUNTY *****")

    # San Bernardino
    print("***** STARTING SAN BERNARDINO COUNTY *****")
    zillowzip_runner("zillow_data.db", "san bernardino county", "ca")
    print("***** FINISH SCRAPING SAN BERNARDINO COUNTY *****")

if __name__ == '__main__':
    main()
