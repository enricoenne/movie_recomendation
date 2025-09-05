# https://github.com/Fitzy1293/letterboxd/blob/main/movies.py

#!/bin/env python3




import requests
import sys
import re
from bs4 import BeautifulSoup
from pprint import pprint
import json
from time import time
from time import sleep, time

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

import pandas as pd


def getMovieRatings(user):
    ratings = {}
    page = 1

    while True:
        if page == 1:
            url = f'https://letterboxd.com/{user}/films/'
        else:
            url = f'https://letterboxd.com/{user}/films/page/{page}/'

        html_text = requests.get(url).text
        soup = BeautifulSoup(html_text, 'html.parser')

        movie_items = soup.select('li.griditem')
        if not movie_items:
            break  # no more movies, exit loop

        for li in movie_items:
            title = li.select_one('img')['alt']
            rating_span = li.select_one('span.rating')
            if rating_span:
                classes = rating_span.get('class', [])
                rated_class = [c for c in classes if c.startswith('rated-')]
                if rated_class:
                    score = int(rated_class[0].split('-')[-1])
                else:
                    score = None
            else:
                score = None

            ratings[title] = score

        page += 1
        sleep(0.1)  # polite delay between pages

    return ratings



if __name__ == '__main__':
    # Example usage:
    ratings = getMovieRatings('enesidemo')
    print(ratings)