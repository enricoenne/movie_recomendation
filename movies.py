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
    data = []
    page = 1
    headers = {"User-Agent": "Mozilla/5.0"}

    while True:
        if page == 1:
            url = f'https://letterboxd.com/{user}/films/'
        else:
            url = f'https://letterboxd.com/{user}/films/page/{page}/'

        html_text = requests.get(url, headers=headers).text
        soup = BeautifulSoup(html_text, 'html.parser')

        movie_items = soup.select('li.griditem')
        if not movie_items:
            break  # no more movies, exit loop

        for li in movie_items:
            title = li.select_one('img')['alt']
            slug = li.select_one('.react-component')['data-item-slug']
            rating_span = li.select_one('span.rating')
            if rating_span:
                classes = rating_span.get('class', [])
                rated_class = [c for c in classes if c.startswith('rated-')]
                if rated_class:
                    score = int(rated_class[0].split('-')[-1])
                else:
                    score = 0
            else:
                score = 0

            data.append({"movie": slug, "rating": score})

        page += 1
        sleep(0.1)  # polite delay between pages

    return data


def get_users_ratings(movie):
    data = []
    page = 1
    headers = {"User-Agent": "Mozilla/5.0"}

    while True:
        if page == 1:
            url = f'https://letterboxd.com/film/{movie}/reviews/by/activity/'
        else:
            url = f'https://letterboxd.com/film/{movie}/reviews/by/activity/page/{page}/'

        html_text = requests.get(url, headers=headers).text
        soup = BeautifulSoup(html_text, 'html.parser')

        reviews = soup.select('div.listitem article')
        if not reviews:
            break  

        for review in reviews:
            # username
            user_link = review.select_one('a.avatar')
            username = user_link['href'].strip('/').split('/')[0] if user_link else None

            # rating
            rating_span = review.select_one('span.rating')
            rating = 0
            if rating_span:
                classes = rating_span.get('class', [])
                rated_class = [c for c in classes if c.startswith('rated-')]
                if rated_class:
                    rating = int(rated_class[0].split('-')[-1])

            data.append({"user": username, "rating": rating})

        page += 1
        sleep(0.1)

    return data


def movie_search(movie, df):
    
    movie_ratings = get_users_ratings(movie)

    if movie not in df.columns:
        df[movie] = pd.NA
    
    for entry in movie_ratings:
        user = entry["user"]
        rating = entry["rating"]
        
        if user not in df.index:
            df.loc[user] = pd.NA
        
        df.at[user, movie] = rating

def movie_search_sparse(movie, df):
    """
    Add all user ratings for a specific movie to the sparse DataFrame.
    
    movie: string, movie slug
    df: sparse DataFrame (users x movies)
    """
    # Step 1: get all user ratings for the movie
    movie_ratings = get_users_ratings(movie)  # returns list of {"user": ..., "rating": ...}
    
    # Step 2: ensure the movie column exists
    if movie not in df.columns:
        df[movie] = 0  # missing ratings = 0
    
    # Step 3: ensure user rows exist and fill ratings
    for entry in movie_ratings:
        user = entry["user"]
        rating = entry["rating"]
        
        if user not in df.index:
            df.loc[user] = 0  # missing ratings = 0
        
        df.at[user, movie] = rating

def user_search(user, df):

    user_ratings = get_movie_ratings(user)

    user_df = pd.DataFrame(user_ratings)

    # if the movie column doesn't exit, it adds it
    for movie in user_df['movie']:
        if movie not in df.columns:
            df[movie] = pd.NA

    if user not in df.index:
        df.loc[user] = pd.NA

    for _, row in user_df.iterrows():
        df.at[user, row["movie"]] = row["rating"]

def user_search_sparse(user, df):
    """
    Add a user's ratings to the sparse DataFrame.
    
    user: string, username
    df: sparse DataFrame (users x movies)
    """
    # Step 1: get the user's ratings
    user_ratings = get_movie_ratings(user)  # returns list of {"movie": slug, "rating": int}
    
    user_df = pd.DataFrame(user_ratings)

    # if the movie column doesn't exit, it adds it
    for movie in user_df['movie']:
        if movie not in df.columns:
            df[movie] = 0

    if user not in df.index:
        df.loc[user] = 0

    for entry in user_ratings:
        movie = entry["movie"]
        rating = entry["rating"]

        # fill in the rating
        df.at[user, movie] = rating


#ratings = get_movie_ratings('enesidemo')
#print(ratings)

#users = get_users('barbie')
#print(users)
    
