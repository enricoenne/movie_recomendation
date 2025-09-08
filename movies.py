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

    return df

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

def user_search_sparse_doesntworkonemptydf(user, df):
    user_ratings = get_movie_ratings(user)  # list of {"movie": ..., "rating": ...}
    
    # Build a temporary DataFrame for this user
    temp_df = pd.DataFrame({entry["movie"]: [entry["rating"]] for entry in user_ratings},
                           index=[user],
                           dtype = 'int8')
    
    # Add missing columns to main df
    for col in temp_df.columns:
        if col not in df.columns:
            df[col] = 0  # sparse int8 column
    
    # Align columns and concatenate
    temp_df = temp_df.reindex(columns=df.columns, fill_value=0)
    
    # Add user row (or overwrite if exists)
    df = pd.concat([df.drop(user, errors='ignore'), temp_df])

def user_search_sparse(user, df):
    user_ratings = get_movie_ratings(user)

    movies = [r['movie'] for r in user_ratings]
    scores = [r["rating"] for r in user_ratings]

    for movie in movies:
        if movie not in df.columns:
            df[movie] = pd.Series([0]*len(df), index=df.index, dtype=pd.SparseDtype("int8", 0))
    
    # create a dense row first
    dense_row = pd.Series(0, index=df.columns, dtype="int8")

    # fill in ratings
    for m, s in zip(movies, scores):
        dense_row[m] = s

    # convert dense row to sparse
    sparse_row = dense_row.astype(pd.SparseDtype("int8", 0))

    # drop old user row if exists
    if user in df.index:
        df = df.drop(user)

    # append new row
    df = pd.concat([df, pd.DataFrame([sparse_row], index=[user])])

    for col in df.columns:
        df[col] = df[col].astype(pd.SparseDtype("int8", 0))

    return df

def get_movie_metadata(movie):
    metadata = {}
    year = None
    mins = None

    headers = {"User-Agent": "Mozilla/5.0"}

    url = f'https://letterboxd.com/film/{movie}/'

    html_text = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html_text, 'html.parser')

    year_tag = soup.select_one("span.releasedate a")
    if year_tag:
        year = int(year_tag.text.strip())
    metadata['year'] = year

    mins_tag = soup.select_one("p.text-link.text-footer")
    if mins_tag:
        text = mins_tag.text.strip()
        # Extract the number before "mins"

        match = re.search(r"(\d+)\s*mins", text)
        if match:
            mins = int(match.group(1))
    metadata['mins'] = mins

    genres = []
    for a in soup.select("div.text-sluglist.capitalize a.text-slug"):
        href = a.get("href", "")
        if href.startswith("/films/genre/"):
            slug = href.replace("/films/genre/", "").strip("/")  # remove /actor/ and trailing slash
            genres.append(slug)
    metadata['genres'] = genres

    directors = []
    for a in soup.select("p.credits span.creatorlist a.contributor"):
        href = a.get("href", "")
        if href.startswith("/director/"):
            slug = href.replace("/director/", "").strip("/")  # remove /director/ and slashes
            name_tag = a.select_one("span.prettify")
            name = name_tag.text.strip() if name_tag else None
            directors.append(slug)
    metadata['directors'] = directors

    actors = []
    for a in soup.select("div.cast-list a.text-slug"):
        href = a.get("href", "")
        if href.startswith("/actor/"):
            slug = href.replace("/actor/", "").strip("/")  # remove /actor/ and trailing slash
            actors.append(slug)
    metadata['actors'] = actors

    return metadata


#ratings = get_movie_ratings('enesidemo')
#print(ratings)

#users = get_users('barbie')
#print(users)

