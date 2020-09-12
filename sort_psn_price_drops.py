#!/usr/bin/env python3

import sys
sys.path.insert(0, './Metacritic-Python-API')

import argparse
import csv

from gameprices.shops import psn
from MetaCriticScraper import MetaCriticScraper

from urllib.request import urlopen, Request
from urllib.parse import quote
from urllib.error import HTTPError

from bs4 import BeautifulSoup


def get_containers(dealContainerAlertsFilename):
    containers = []
    with open(dealContainerAlertsFilename) as csvfile:
        containersReader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for row in containersReader:
            container = {}
            container['containerId'] = row[0]
            container['store'] = row[1]
            containers.append(container)

    return containers


def get_response(req):
    try:
        return urlopen(req)
    except HTTPError as e:
        if e.code == 429:
            time.sleep(5)
            return get_response(req)
        raise


def find_game(game_name):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) '
                             'Chrome/41.0.2228.0 Safari/537.3'}

    # hardcoded PS4 platform - may be extended easily
    search_url = "https://www.metacritic.com/search/game/" + \
                 quote(game_name.replace('’', "'")).replace('/', '-') + \
                 "/results?plats[72496]=1&search_type=advanced"

    req = Request(url=search_url, headers=headers)

    response = get_response(req)
    soup = BeautifulSoup(response.read(), 'html.parser')
    return soup.find("li", class_="result first_result")


def get_metacritic_ratings(games):
    games_ratings = set()

    for game_name in games:
        print("Current game: " + game_name)

        first_result = find_game(game_name)
        str_split = game_name.rsplit(' ', 1)
        while first_result is None and len(str_split) > 1:
            first_result = find_game(str_split[0])
            str_split = str_split[0].rsplit(' ', 1)

        if first_result is None:
            print("No such game in Metacritic database")
            continue

        first_result_li = first_result.a['href']
        metacritic_game_url = "https://www.metacritic.com/" + first_result_li + "?ref=hp"
        scraper = MetaCriticScraper(metacritic_game_url)

        if scraper.game['critic_score']:
            critic_score = int(scraper.game['critic_score'])
        else:
            critic_score = 0

        if scraper.game['user_score'] and scraper.game['user_score'] != 'tbd':
            user_score = float(scraper.game['user_score'])
        else:
            user_score = 0

        games_ratings.add((scraper.game['title'], user_score, critic_score))
    return games_ratings


def sort_ratings(ratings):
    ratings_list = list(ratings)

    # by user score first and then by critic for equal user scores
    sorted_user_critic = sorted(ratings_list, key=lambda rating: rating[1] * 1000 + rating[2], reverse=True)

    # by critic score first and then by user for equal critic scores
    sorted_critic_user = sorted(ratings_list, key=lambda rating: rating[2] * 10 + rating[1], reverse=True)

    return sorted_user_critic, sorted_critic_user


def check_containers(containers):
    for container in containers:
        containerId = container['containerId']
        store = container['store']

        items = psn._get_items_by_container(
            containerId, store, {"platform": "ps4"})

        names = []
        if (items is None):
            print(
                "No items found for Container '" +
                containerId +
                "' in store " +
                store)
        else:
            for subsetStartIdx in range(0, len(items), 3):
                itemsSubset = items[subsetStartIdx: subsetStartIdx + 3]
                for item in itemsSubset:
                    names.append(psn._get_name(item))

        ratings = get_metacritic_ratings(names)
        sorted_user, sorted_critic = sort_ratings(ratings)

        print("\nSorted by User Score:")
        for rating in sorted_user:
            print("\nTitle: " + str(rating[0]) + "\nUser Score: " + str(rating[1]) +
                  " Critic Score: " + str(rating[2]))

        print("\nSorted by Critic Score:")
        for rating in sorted_critic:
            print("\nTitle: " + str(rating[0]) + "\nCritic Score: " + str(rating[2]) +
                  " User Score: " + str(rating[1]))



def main(clargs):
    containers = get_containers(str(clargs.drops))
    check_containers(containers)
    print("\nFinished processing")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='''''')
    parser.add_argument('--drops', required=True,
                        help='Price drops descriptor')
    main(parser.parse_args())
