from bs4 import BeautifulSoup
from requests import Session, RequestException
from json import loads
from html import unescape
from typing import Optional
from datetime import datetime
from headers import Headers, Proxies
import sqlite3


def scrape_page(session: Session, url: str) -> list:
    '''
    Generator to yield scraped properties on each page 

    Args:
        session (Session): requests session to maintain continuity across requests
        url (str): Zillow URL to scrape

    Yields:
        list: List containing all of the scraped properties, each as a dictionary (JSON).
              Prints the number of pages scraped and the total number of properties scraped.
    '''
    
    pages = [url]
    
    # Initial request, checks if the response is successful
    response = session.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, "html.parser").select("#__NEXT_DATA__")
        page_data = loads(soup[0].getText())['props']['pageProps']['searchPageState']['cat1']
        
        # Yield cleaned data for each property on the first page
        properties = page_data['searchResults']['listResults']
        
        for property_info in properties:
            yield property_info

        # Handle pagination
        pagination = page_data['searchList']['pagination']
        while pagination and 'nextUrl' in pagination:
            next_url = 'https://www.zillow.com' + pagination['nextUrl']
            response = session.get(next_url)
            pages.append(next_url)
            soup = BeautifulSoup(response.content, "html.parser").select("#__NEXT_DATA__")
            page_data = loads(soup[0].getText())['props']['pageProps']['searchPageState']['cat1']
            
            # Yield cleaned data for each property on each subsequent page
            properties = page_data['searchResults']['listResults']
            for property_info in properties:
                yield property_info

            pagination = page_data['searchList']['pagination']

        print(f"{len(pages)} pages from {url}")




def clean_data(property_info : dict) -> dict:
    '''
    Cleans a dictionary of property data and returns a new dictionary
    containing only the important features, including a custom calculated
    features and formatted dates.

    Args:
        property_info (dict): input dictionary with property info (json)

    Returns:
        dict: dictionary containing these house features
              (zpid, streetaddress, city, statezipcode,
               price, sqft, price_per_sqft, home_type,
               date_sold, bath, bed, lot_area, lot_area_unit,
               link, latitude, longitude, date_scraped)
    '''

    house = property_info

    info = {
        "zpid": house.get('hdpData', {}).get('homeInfo', {}).get('zpid'),
        "streetaddress": house.get('addressStreet'),
        "city": house.get('addressCity'),
        "state": house.get('addressState'),
        "zipcode": house.get('addressZipcode'),
        "home_status": house.get('statusType'),
        "price": house.get('hdpData', {}).get('homeInfo', {}).get('price'),
        "sqft": house.get('hdpData', {}).get('homeInfo', {}).get('livingArea'),
        "price_per_sqft": (house.get('hdpData', {}).get('homeInfo', {}).get('price') /
                           (house.get('hdpData', {}).get('homeInfo', {}).get('livingArea'))
                           if house.get('hdpData', {}).get('homeInfo', {}).get('price') and
                           house.get('hdpData', {}).get('homeInfo', {}).get('livingArea') else None),
        "home_type": house.get('hdpData', {}).get('homeInfo', {}).get('homeType'),
        "date_sold": (datetime.fromtimestamp(house.get('hdpData', {}).get('homeInfo', {}).get('dateSold') /
                      1000).strftime("%Y-%m-%d") if house.get('hdpData', {}).get('homeInfo', {}).get('dateSold') else None),
        "bath": house.get('hdpData', {}).get('homeInfo', {}).get('bathrooms'),
        "bed": house.get('hdpData', {}).get('homeInfo', {}).get('bedrooms'),
        "lot_area" : house.get('hdpData', {}).get('homeInfo', {}).get('livingArea'),
        "lot_area_unit": house.get('hdpData', {}).get('homeInfo', {}).get('lotAreaUnit'),
        "link": house.get('detailUrl'),
        "latitude": house.get('latLong', {}).get('latitude'),
        "longitude": house.get('latLong', {}).get('longitude'),
        "date_scraped": datetime.now().strftime("%Y-%m-%d")
    }
    return info



def get_properties(session: Session, zipcode: int) -> list:
    """
    Scrapes and cleans properties from both for sale and sold pages

    Args:
        session (requests.Session): Requests session
        zipcode (int): 5-digit zipcode

    Returns:
        list: list containing dictionaries of cleaned data
    """

    data = []

    for_sale_url = f"https://www.zillow.com/{zipcode}"
    sold_url = f"https://www.zillow.com/{zipcode}/sold"

    
    # scrapes from url, and cleans the data
    for url in [for_sale_url, sold_url]:
        for property_info in scrape_page(session, url):
            data.append(clean_data(property_info))
    
    return data



def ingest_to_db(db_name: str, data: list):
    """
    Inserts cleaned property data into an SQLite database.

    Args:
        db_name (str): database name 
        data (list): a list containing cleaned property data
    
    """
    # Create connection to the database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS properties (
            zpid TEXT PRIMARY KEY,
            streetaddress TEXT,
            city TEXT,
            state TEXT,
            zipcode TEXT,
            home_status TEXT,
            price REAL,
            sqft REAL,
            price_per_sqft REAL,
            home_type TEXT,                  
            date_sold TEXT,
            bath REAL,
            bed REAL,
            lot_area REAL,                 
            lot_area_unit TEXT,
            link TEXT,
            latitude REAL,
            longitude REAL,
            date_scraped TEXT
        )
    ''')
    
    # Insert data
    cursor.executemany('''
        INSERT OR REPLACE INTO properties VALUES (
            :zpid, :streetaddress, :city, :state, :zipcode, :home_status,
            :price, :sqft, :price_per_sqft, :home_type, :date_sold,
            :bath, :bed, :lot_area, :lot_area_unit, :link,
            :latitude, :longitude, :date_scraped
        )
    ''', data)
    
    conn.commit()
    conn.close()



def zillow_zipcode_to_db(zipcode: int, db_name: str = "zillow_data.db"):
    '''
    Scrapes zillow for sold and for sale properties and ingests it
    into a SQLite database

    Args:
        zipcode (int): 5-digit US zipcode
        db_name (str): a specified database name
    '''
    headers = Headers()
    
    with Session() as session:
        session.headers.update(headers.get())
        
        # Get and clean properties
        data = get_properties(session, zipcode)
        
        # Ingest into the database
        ingest_to_db(db_name, data)

    print(f"Ingested {len(data)} properties into {db_name}")




def scrape_zillow_city(city: str, state: str) -> list:
    '''
    Scrapes a Zillow city page of both sold and for sale properties,
    collecting data across all paginated pages using the same session.

    Args: 
        city (str): city
        state (str): 2 character state code

    Returns:
        list: List containing cleaned property data for all scraped properties
    '''

    headers = Headers()
    cleaned_data = []

    for_sale_url = f"https://www.zillow.com/{city}-{state}"
    sold_url = f"https://www.zillow.com/{city}-{state}/sold"
    
    # Create a session to scrape both URLs
    with Session() as session:
        session.headers.update(headers.get())  # Set headers for the session
        
        # Scrape for sale and sold properties using the same session
        for_sale_data = scrape_page(session, for_sale_url)
        sold_data = scrape_page(session, sold_url)
        
        # Combine the data
        data = sold_data + for_sale_data

        # Clean data for each property
        for property in data:
            cleaned_data.append(clean_data(property))

    print(f"Total of {len(cleaned_data)} properties scraped!")

    return cleaned_data
