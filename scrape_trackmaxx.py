#!/usr/bin/env python

import datetime

from bs4 import BeautifulSoup
import requests


class ResultData:
    def __init__(self):
        self.start_number = ''
        self.category = ''
        self.time_str = ''
        self.time_seconds = 0.0

    def __str__(self):
        items = []
        items.append(self.start_number)
        items.append(self.category)
        items.append(self.time_str)
        items.append(str(self.time_seconds))
        return ','.join(items)


class ScrapeTrackMaxx:
    def __init__(self, race_id='', cat_ids=[]):
        self.race_id = race_id
        self.cat_ids = cat_ids
        self.data = []

    def fetch_data(self):
        self.data = []
        for run_id in self.cat_ids:
            i = 0
            url = f'https://trackmaxx.ch/results/?race={self.race_id}&c={run_id}&p='
            while self._fetch_data(url + str(i)):
                i += 1
        return self.data

    def _fetch_data(self, url):
        req = requests.get(url)
        soup = BeautifulSoup(req.text, 'html.parser')
        results_table = soup.find(id='tbodyresults')
        for row in results_table.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) > 4:
                rd = ResultData()
                rd.start_number = cols[8].text
                rd.category = cols[9].text
                rd.time_str = cols[5].text
                if rd.category != '':
                    rd.category = rd.category.split(':')[0]
                    time = datetime.datetime.strptime(rd.time_str, "%H:%M:%S")
                    minutes = time.hour * 60 + time.minute
                    rd.time_seconds = minutes * 60 + time.second
                    self.data.append(rd)
                else:
                    return False
        return True


scraper = ScrapeTrackMaxx(race_id='gsl20', cat_ids=['bc0b7426-be6d-4edd-8460-936b3c3d5460', 'd6c89c35-e9a9-4b66-a5b5-61e111d3c378'])
data = scraper.fetch_data()
print('start_number,category,time_str,time_seconds')
for item in data:
    print(item)
