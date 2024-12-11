from bs4 import BeautifulSoup
from requests import Session, RequestException, get
from json import loads
from html import unescape
from typing import Optional, Generator, Union
from datetime import datetime
from headers import Headers, Proxies
import sqlite3

class ZillowScraper():


    def __init__(self):
        self.headers = Headers()
        self.session = None
        self.db = None
        self.total_properties = 0
        self.pages = []
        self.data = []
    

    def scrape_page(self, url: str):
        """
        Scrape data from Zillow and yield each property as it is found.
        """
        self.pages.append(url)
        
        # Initial request, checks if the response is successful
        if self.session:
            response = self.session.get(url)
        else:
            response = get(url, headers = self.headers.get())
        
        if response.status_code == 200:
            properties, pagination = self._parse_page(response)
            
            # Yield data from page
            for property_info in properties:
                yield property_info
            
            # Starts request for the next page if there is one
            while pagination and 'nextUrl' in pagination:
                next_url = 'https://www.zillow.com' + pagination['nextUrl']
                self.pages.append(next_url)
                response = self.session.get(next_url)

                properties, pagination = self._parse_page(response)
                
                # Yield data from page
                for property_info in properties:
                    yield property_info

            print(f"{len(self.pages)} pages from {url}")


    def _parse_page(self, response):
        '''
        Parses page using BeautifulSoup and returns page data regarding
        properties and pagination
        '''

        soup = BeautifulSoup(response.content, "html.parser").select("#__NEXT_DATA__")
        page_data = loads(soup[0].getText())['props']['pageProps']['searchPageState']['cat1']

        properties = page_data['searchResults']['listResults']
        pagination = page_data['searchList']['pagination']

        return properties, pagination


    def _clean_data(self, data: dict) -> dict:
        info = {
            "zpid": data.get('hdpData', {}).get('homeInfo', {}).get('zpid'),
            "streetaddress": data.get('addressStreet'),
            "city": data.get('addressCity'),
            "state": data.get('addressState'),
            "zipcode": data.get('addressZipcode'),
            "home_status": data.get('statusType'),
            "price": data.get('hdpData', {}).get('homeInfo', {}).get('price'),
            "sqft": data.get('hdpData', {}).get('homeInfo', {}).get('livingArea'),
            "price_per_sqft": (data.get('hdpData', {}).get('homeInfo', {}).get('price') /
                            (data.get('hdpData', {}).get('homeInfo', {}).get('livingArea'))
                            if data.get('hdpData', {}).get('homeInfo', {}).get('price') and
                            data.get('hdpData', {}).get('homeInfo', {}).get('livingArea') else None),
            "home_type": data.get('hdpData', {}).get('homeInfo', {}).get('homeType'),
            "date_sold": (datetime.fromtimestamp(data.get('hdpData', {}).get('homeInfo', {}).get('dateSold') /
                        1000).strftime("%Y-%m-%d") if data.get('hdpData', {}).get('homeInfo', {}).get('dateSold') else None),
            "bath": data.get('hdpData', {}).get('homeInfo', {}).get('bathrooms'),
            "bed": data.get('hdpData', {}).get('homeInfo', {}).get('bedrooms'),
            "lot_area" : data.get('hdpData', {}).get('homeInfo', {}).get('livingArea'),
            "lot_area_unit": data.get('hdpData', {}).get('homeInfo', {}).get('lotAreaUnit'),
            "link": data.get('detailUrl'),
            "latitude": data.get('latLong', {}).get('latitude'),
            "longitude": data.get('latLong', {}).get('longitude'),
            "date_scraped": datetime.now().strftime("%Y-%m-%d")
        }
        return info


    def _get_properties(self, area: Union[str, int]) -> list:

        # Preparing the urls for for sale and sold zillow pages
        for_sale_url = f"https://www.zillow.com/{area}"
        sold_url = f"https://www.zillow.com/{area}/sold"

        
        # Scrapes from url, and cleans the data
        for url in [for_sale_url, sold_url]:
            for property_info in self.scrape_page(url):
                self.data.append(self._clean_data(property_info))


    def _ingest_to_db(self) -> None:
        conn = sqlite3.connect(self.db)
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
        ''', self.data)

        print(f"Ingested {len(self.data)} rows into {self.db}")

        # Keep count of properties scraped
        self.total_properties += len(self.data)
        self.data = []
        conn.commit()
        conn.close()


    def set_db(self, db: str) -> None:
        self.db = db
        print(f"Set database to {db}")
    

    def scrape_zipcode_to_db(self, zipcode: int):
        if not self.db:
            raise AttributeError("No database set. Set data base with set_db()")
        self.headers = Headers()
        self.session = Session()
        self.session.headers.update(self.headers.get())
        self._get_properties(zipcode)
        self._ingest_to_db()
        self.pages = []

    
    def scrape_city_to_db(self, city: str, state: str):
        if not self.db:
            raise AttributeError("No database set. Set data base with set_db()")
        self.headers = Headers()
        self.session = Session()
        self.session.headers.update(self.headers.get())
        self._get_properties(f"{city}-{state}")
        self._ingest_to_db()
        self.pages = []
