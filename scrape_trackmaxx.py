#!/usr/bin/env python

import datetime
import re
import sys

from bs4 import BeautifulSoup
import requests


class TimeEntry:
    def __init__(self):
        self.name = ''
        self.distance_km = 0.0
        self.time_str = ''
        self.time_seconds = 0.0
        self.pace = ''
        self.overall_rank = ''
        self.category_rank = ''

    def __str__(self):
        items = []
        items.append(self.name)
        items.append(str(self.distance_km))
        items.append(self.time_str)
        if self.time_seconds:
            items.append(str(self.time_seconds))
        else:
            items.append('')
        items.append(self.pace)
        items.append(self.overall_rank)
        items.append(self.category_rank)
        return ','.join(items)


class ResultData:
    def __init__(self):
        self.start_number = ''
        self.category = ''
        self.time_entry = TimeEntry()
        self.sub_time_entries = []
        self.overall_total = ''
        self.category_total = ''

    def __str__(self):
        items = []
        items.append(self.start_number)
        items.append(self.category)
        items.append(str(self.time_entry.distance_km))
        items.append(self.time_entry.time_str)
        items.append(str(self.time_entry.time_seconds))
        items.append(self.time_entry.pace)
        items.append(self.time_entry.overall_rank)
        items.append(self.overall_total)
        items.append(self.time_entry.category_rank)
        items.append(self.category_total)
        res = ','.join(items)
        for sub in self.sub_time_entries:
            res += ',' + str(sub)
        return res


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
                    rd.time_seconds = self._time_str_to_seconds(rd.time_str)
                    self._fetch_detail_data(rd)
                    self.data.append(rd)
                    return True
                else:
                    return False
        return True

    def _fetch_detail_data(self, rd):
        url = f'https://trackmaxx.ch/list/detail_results2.ashx?r={self.race_guid}&o={rd.start_number}&l=de'
        req = requests.get(url)
        data = req.json()

        res = re.match(r'Running (\d+\.\d)km', data['participantinfos'][7]['value'])
        if res:
            rd.time_entry.distance_km = float(res[1])

        # get the precise time...
        rd.time_entry.time_str = data['participantinfos'][10]['value'].replace(',', '.')
        rd.time_entry.time_seconds = self._time_str_to_seconds(rd.time_entry.time_str)

        rd.time_entry.pace = data['participantinfos'][11]['value']
        cat_value = data['participantinfos'][12]['value']
        res = re.match(r'(\d+)\. von (\d+)', cat_value)
        if res:
            rd.time_entry.category_rank = res[1]
            rd.category_total = res[2]

        overall_value = data['participantinfos'][13]['value']
        res = re.match(r'(\d+)\. von (\d+)', overall_value)
        if res:
            rd.time_entry.overall_rank = res[1]
            rd.overall_total = res[2]

        # parse sub track[1..n] items
        try:
            self._get_sub_track_data(data, rd)
        except Exception:
            print(f'problem with parsing data: {data}', file=sys.stderr)
            raise

    def _datetime_to_seconds(self, time):
        minutes = time.hour * 60 + time.minute
        return minutes * 60 + time.second + time.microsecond / 1e6

    def _time_str_to_seconds(self, time_str):
        # ignore empty values for now
        if time_str is None or time_str == '':
            return None

        time = None
        time_fmts = ['%H:%M:%S', '%M:%S', '%H:%M:%S.%f']
        for time_fmt in time_fmts:
            try:
                time = datetime.datetime.strptime(time_str, time_fmt)
            except Exception:
                pass

        assert time is not None, f'failed to parse {time_str}'
        return self._datetime_to_seconds(time)

    def _get_sub_track_data(self, data, rd):
        tracks = data['track']
        # skip the first one, it's at 0 km
        for i in range(1, len(tracks)):
            track = tracks[i]
            te = TimeEntry()
            te.name = track['caption']
            te.distance_km = track['distance']
            rd.sub_time_entries.append(te)
            # don't try to assign things from empty items
            if 'runtime' in track and track['runtime'] != '':
                try:
                    te.time_str = track['runtime']
                    te.time_seconds = self._time_str_to_seconds(te.time_str)
                    te.pace = track['speed']
                    te.overall_rank = track['rank2'].replace('.', '')
                    te.category_rank = track['rank1'].replace('.', '')
                except Exception:
                    print(f'problem with track data: {track}', file=sys.stderr)
                    raise


scraper = ScrapeTrackMaxx(race_id='gsl20', cat_ids=['bc0b7426-be6d-4edd-8460-936b3c3d5460', 'd6c89c35-e9a9-4b66-a5b5-61e111d3c378'], race_guid='9df022e2-76c6-45cb-9140-f70883fbbb25')
data = scraper.fetch_data()

header = 'start_number,category,distance_km,time_str,time_seconds,pace,overall_rank,overall_total,category_rank,category_total'
if len(data) > 0:
    time_entries = data[0].sub_time_entries
    for i in range(len(time_entries)):
        header += f',segment_name_{i},segment_distance_km_{i},segment_time_str_{i},segment_time_seconds_{i},segment_pace_{i},segment_overall_rank_{i},segment_category_rank_{i}'
print(header)

for item in data:
    print(item)
