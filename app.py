#!/usr/bin/env python3
import logging
import sys
from functools import lru_cache, wraps
from time import monotonic_ns

import requests
from flask import Flask, request

app = Flask('nba')

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] %(message)s',  # %(name)s
    datefmt='%d/%m/%Y %H:%M:%S'
)
log = logging.getLogger('nba')

# https://blog.soumendrak.com/cache-heavy-computation-functions-with-a-timeout-value
def timed_lru_cache(_func=None, *, seconds: int = 7000, maxsize: int = None, typed: bool = False):
    """ Extension over existing lru_cache with timeout
    :param seconds: timeout value
    :param maxsize: maximum size of the cache
    :param typed: whether different keys for different types of cache keys
    """

    def wrapper_cache(f):
        # create a function wrapped with traditional lru_cache
        f = lru_cache(maxsize=maxsize, typed=typed)(f)
        # convert seconds to nanoseconds to set the expiry time in nanoseconds
        f.delta = seconds * 10 ** 9
        f.expiration = monotonic_ns() + f.delta

        @wraps(f)  # wraps is used to access the decorated function attributes
        def wrapped_f(*args, **kwargs):
            if monotonic_ns() >= f.expiration:
                # if the current cache expired of the decorated function then
                # clear cache for that function and set a new cache value with new expiration time
                f.cache_clear()
                f.expiration = monotonic_ns() + f.delta
            return f(*args, **kwargs)

        wrapped_f.cache_info = f.cache_info
        wrapped_f.cache_clear = f.cache_clear
        return wrapped_f

    # To allow decorator to be used without arguments
    if _func is None:
        return wrapper_cache
    else:
        return wrapper_cache(_func)

def aggregate_blocklists(blocklists: list):
    aggregated_blocklists = ""
    for blocklist in blocklists:
        aggregated_blocklists += requests.get(blocklist).text + "\n"
    return aggregated_blocklists

@timed_lru_cache(seconds=60*60*24)
def get_configuration_blocklists(configuration_id: str, api_key: str):
    blocklist_url_template = "https://raw.githubusercontent.com/nextdns/metadata/master/privacy/blocklists/%s.json"
    blocklist_urls = []
    headers = {
        "X-Api-Key": api_key
    }

    configuration_blocklists = requests.get(f"https://api.nextdns.io/profiles/{configuration_id}", headers=headers).json()["data"]["privacy"]["blocklists"]
    for blocklist in configuration_blocklists:
        blocklist_data = requests.get(blocklist_url_template % blocklist["id"]).json()
        if "source" in blocklist_data:
            blocklist_urls.append(blocklist_data["source"]["url"])
        elif "sources" in blocklist_data:
            for source in blocklist_data["sources"]:
                blocklist_urls.append(source["url"])

    return blocklist_urls

@app.route("/<string:configuration_id>", methods=["GET"])
def _aggregated_configuration(configuration_id: str):
    api_key = request.args.get("api_key")
    if not api_key:
        return f"<b>Error: </b>Missing required query parameter <code>api_key</code>.</h1>"

    configuration_blocklists = get_configuration_blocklists(configuration_id, api_key)
    aggregated_blocklists = aggregate_blocklists(configuration_blocklists)
    return aggregated_blocklists, 200, {'Content-Type': 'text/plain; charset=utf-8'}

if __name__ == "__main__":
    app.config["DEBUG"] = True
    app.run(host="0.0.0.0", port=8080)
