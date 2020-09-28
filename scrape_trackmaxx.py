#!/usr/bin/env python

import datetime
import re

from bs4 import BeautifulSoup
import requests


class ResultData:
    def __init__(self):
        self.start_number = ''
        self.category = ''
        self.time_str = ''
        self.time_seconds = 0.0
        self.pace = ''
        self.overall_rank = ''
        self.overall_total = ''
        self.category_rank = ''
        self.category_total = ''

    def __str__(self):
        items = []
        items.append(self.start_number)
        items.append(self.category)
        items.append(self.time_str)
        items.append(str(self.time_seconds))
        items.append(self.pace)
        items.append(self.overall_rank)
        items.append(self.overall_total)
        items.append(self.category_rank)
        items.append(self.category_total)
        return ','.join(items)


class ScrapeTrackMaxx:
    def __init__(self, race_id='', cat_ids=[], race_guid=''):
        self.race_id = race_id
        self.cat_ids = cat_ids
        self.race_guid = race_guid
        self.data = []

    def fetch_data(self):
        self.data = []
        for run_id in self.cat_ids:
            i = 0
            while self._fetch_data(run_id, i):
                i += 1
        return self.data

    def _fetch_data(self, run_id, page):
        url = f'https://trackmaxx.ch/results/?race={self.race_id}&c={run_id}&p={str(page)}'
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
                    self._fetch_detail_data(rd)
                    self.data.append(rd)
                else:
                    return False
        return True

    def _fetch_detail_data(self, rd):
        url = f'https://trackmaxx.ch/list/detail_results2.ashx?r={self.race_guid}&o={rd.start_number}&l=de'
        req = requests.get(url)
        data = req.json()

        # get the precise time...
        rd.time_str = data['participantinfos'][10]['value'].replace(',', '.')
        time = datetime.datetime.strptime(rd.time_str, "%H:%M:%S.%f")
        minutes = time.hour * 60 + time.minute
        rd.time_seconds = minutes * 60 + time.second + time.microsecond / 1e6

        rd.pace = data['participantinfos'][11]['value']
        cat_value = data['participantinfos'][12]['value']
        res = re.match(r'(\d+)\. von (\d+)', cat_value)
        if res:
            rd.category_rank = res[1]
            rd.category_total = res[2]

        overall_value = data['participantinfos'][13]['value']
        res = re.match(r'(\d+)\. von (\d+)', overall_value)
        if res:
            rd.overall_rank = res[1]
            rd.overall_total = res[2]

        # TODO parse track[1..n] items


scraper = ScrapeTrackMaxx(race_id='gsl20', cat_ids=['bc0b7426-be6d-4edd-8460-936b3c3d5460', 'd6c89c35-e9a9-4b66-a5b5-61e111d3c378'], race_guid='9df022e2-76c6-45cb-9140-f70883fbbb25')
data = scraper.fetch_data()
print('start_number,category,time_str,time_seconds,pace,overall_rank,overall_total,category_rank,category_total')
for item in data:
    print(item)
