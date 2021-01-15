import requests
import json
import html
import os
import numpy as np
from time import sleep
import random
import urllib
from bs4 import BeautifulSoup

imdbUrl = "https://www.imdb.com/search/title/?title_type=feature,tv_movie&user_rating=3.0,9.5&num_votes=10000,&sort=user_rating,desc&count=250&"
rotten_url = "https://www.rottentomatoes.com/api/private/v2.0/search?q="

headers = {'Accept-Language': 'en-US,en;q=0.8'}


dataList = [dict() for x in range(50)]


def getMovieURLs(url):
    data = {}
    r = requests.get(url=url, headers=headers)

    # Create a BeautifulSoup object
    soup = BeautifulSoup(r.text, 'html.parser')
    link = list(soup.find_all("h3"))

    arrayURL = []
    try:
        for i in range(1, 250, 5):
            arrayURL.append(link[i].find("a").get("href"))
        pass
    except:
        pass
    return arrayURL


def getMovieDetails(url):
    data = {}
    r = requests.get(url="https://www.imdb.com"+url, headers=headers)
    # Create a BeautifulSoup object
    soup = BeautifulSoup(r.text, 'html.parser')

    # page title
    title = soup.find('title')
    data["title"] = html.unescape(title.string)

    # rating
    ratingValue = soup.find("span", {"itemprop": "ratingValue"})
    data["ratingValue"] = float(ratingValue.string)

    # no of rating given
    ratingCount = soup.find("span", {"itemprop": "ratingCount"})
    data["ratingCount"] = int(ratingCount.string.string.replace(',', ''))

    # year
    try:
        data["year"] = int(
            data["title"][data["title"].rfind("(")+1:data["title"].rfind(")")])
        pass
    except:
        data["year"] = int(data["title"][data["title"].rfind(
            "(TV Movie ")+10:data["title"].rfind(")")])
    # budget
    try:
        budget = soup.find("h4", string="Budget:").next_sibling
        data["budget"] = budget.string.strip()
        pass
    except:
        data["budget"] = "N/A"

    # gross
    try:
        gross = soup.find(
            "h4", string="Cumulative Worldwide Gross:").next_sibling
        data["gross"] = gross.string.strip()
        pass
    except:
        data["gross"] = "N/A"

    # country
    try:
        country = soup.find("h4", string="Country:").next_sibling.next_sibling
        data["country"] = country.string.strip()
        pass
    except:
        data["country"] = "N/A"

    # name
    titleName = soup.find("div", {'class': 'titleBar'}).find("h1")
    data["name"] = html.unescape(titleName.contents[0].replace(u'\xa0', u''))

    # rotten tomatoes score
    r2 = requests.get(
        url=(rotten_url+urllib.parse.quote(data["name"], safe='')))
    tomatoData = json.loads(r2.text)
    tomatoMeter = -1
    try:
        for tomato in tomatoData['movies']:
            if (tomato["name"].lower().find(data["name"].lower()) != -1 and tomato["year"] == data["year"]):
                tomatoMeter = tomato["meterScore"]
                data["tomatoMeter"] = tomatoMeter
                break
        if (tomatoMeter == -1):
            data["tomatoMeter"] = None
        pass
    except:
        data["tomatoMeter"] = None
        pass

    # runtime
    try:
        runtime = soup.find("h4", string="Runtime:").next_sibling.next_sibling
        runtime = runtime.string.strip()
        mins = runtime[0:runtime.find("min")-1]
        data["runtime"] = int(mins)
        pass
    except:
        runtime = "N/A"


    # genres
    genres = soup.find("h4", string="Genres:")
    data["genres"] = []
    for sibling in genres.next_siblings:
        genre = sibling.string.strip()
        if (genre != "" and genre != "|"):
            data["genres"].append(genre)


    try:
        credit_summary_item = soup.find_all(
            "div", {'class': 'credit_summary_item'})
        #data["credits"] = {}
        for i in credit_summary_item:
            item = i.find("h4")
            names = i.find_all("a")
            # data["credits"][item.string] = []
            data[item.string] = []
            for i in names:
                # data["credits"][item.string].append({
                data[item.string].append({
                    "link": i["href"],
                    "name": i.string
                })
        pass
    except:
        pass

    return data


def do_scrape(output_file, pages):

    flush_threshold = 5
    buffered_item_count = 0

    for page in pages:
        movie_urls = getMovieURLs(imdbUrl+"start="+str(page)+"&ref_=adv_nxt")
        movie_urls_length = len(movie_urls)

        print(f'Page #{page}: {movie_urls_length} movies')
        
        for index, url in enumerate(movie_urls):
            movie_details = getMovieDetails(url)

            print(f'[{index+1}/{movie_urls_length}] {movie_details["title"]}')
            #sleep(random.randint(0, 2))

            data_json = json.dumps(movie_details, ensure_ascii=False)

            output_file.write(data_json)

            # End of json object
            output_file.write(',')

            # Flush written content to file if needed
            buffered_item_count = buffered_item_count + 1
            if buffered_item_count >= flush_threshold:
                output_file.flush()
                buffered_item_count = 0
        
        print('\n')



def main():
    resume = True
    start_page = 1

    pages = np.arange(start_page, 8502, 250)
    print(pages)

    # Open output file
    with open("movies_raw.json", "r+", encoding='utf8') as f:
        if resume:
            f.seek(0, os.SEEK_END)
        else:
            # Open json array
            f.write('[')

        do_scrape(f, pages)

        # Close json array
        f.write(']')


    # Open output file for json correction
    with open("movies_raw.json", "r+b") as f:
        f.seek(-2, os.SEEK_END)
        f.write(b']')
        f.truncate()

main()
