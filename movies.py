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


def get_movie_ratings(user):
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

def get_users(movie):
    users = []
    page = 1

    while True:
        if page == 1:
            url = f'https://letterboxd.com/film/{movie}/reviews/by/activity/'
        else:
            url = f'https://letterboxd.com/film/{movie}/reviews/by/activity/page/{page}/'

        

        html_text = requests.get(url).text
        soup = BeautifulSoup(html_text, 'html.parser')

        reviews = soup.select('div.listitem article')

        if not reviews:
            break  # no more movies, exit loop

        for div in reviews:
            # Find the avatar link, extract username from href
            user_link = div.select_one('a.avatar')
            if user_link:
                username = user_link['href'].strip('/').split('/')[0]
                users.append(username)
        
        page += 1
        sleep(0.1)  # polite delay between pages

    return users


#ratings = get_movie_ratings('enesidemo')
#print(ratings)

#users = get_users('barbie')
#print(users)
    
