#!/usr/bin/env python3

import requests
import pprint
import itertools
from xml.etree import ElementTree
from flask import Flask, render_template, Markup, escape
from jinja2 import evalcontextfilter
import re
import time
import datetime
from collections import defaultdict, OrderedDict

url = "http://www.tokyoartbeat.com/events/xml.php?lang=en&contentType={}"

areas = [
    "Shinjuku",
    "Shibuya",
    "GinzaMarunouchi",
    "UenoYanaka",
    "KyobashiNihonbashi",
    "OmotesandoAoyama",
    "RoppongiNogizaka",
    "EbisuDaikanyama",
    "Chiyoda"
]

last_check = None

partydata = defaultdict(lambda: defaultdict(list))

def add_area(partydata, area):
    response = requests.get(url.format(area))
    tree = ElementTree.fromstring(response.content)
    today = datetime.date.today()
    today_tuple = (today.year, today.month, today.day)

    for e in tree.findall(".//Event"):
        event_parties = e.findall("Party")
        if event_parties:
            for p in event_parties:
                date = p.get("date")
                date_tuple = tuple(map(int, date.split("-")))

                if date_tuple >= today_tuple:
                    v = e.find("Venue")
                    venue = {
                        "name": v.find("Name").text,
                        "address": v.find("Address").text,
                        "lat": e.find("Latitude").text,
                        "long": e.find("Longitude").text
                    }
                    images = [i.get("src") for i in e.findall("Image")]
                    party = {
                        "href": e.get("href"),
                        "description": e.find("Description").text,
                        "date": date_tuple,
                        "start": p.get("start"),
                        "type": p.text,
                        "end": p.get("end"),
                        "name": e.find("Name").text,
                        "images": images,
                        "venue": venue
                    }

                    area_formatted = re.sub(r"(\w)([A-Z])", r"\1 / \2", area)

                    partydata[date_tuple][area_formatted].append(party)

    return partydata


app = Flask(__name__)

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')
@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
        for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result


def create_app():

    app = Flask(__name__)
    _paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')
    @app.template_filter()
    @evalcontextfilter
    def nl2br(eval_ctx, value):
        result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
            for p in _paragraph_re.split(escape(value)))
        if eval_ctx.autoescape:
            result = Markup(result)
        return result

    @app.route("/")
    def home():
        global last_check
        global partydata
        if last_check is None or time.time() - last_check > 8 * 60 * 60:
            last_check = time.time()
            partydata = defaultdict(lambda: defaultdict(list))
            for area in areas:
                partydata = add_area(partydata, area)


        return render_template("index.tmpl", partydata=sorted(partydata.items()))

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
