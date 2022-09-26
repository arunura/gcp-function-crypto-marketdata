import functions_framework
import requests
import time
import os
from time import sleep
from threading import Lock

# Dictionary of url to response text
response_cache_dict = {}

# Rate limit the requests to a CoinGecko url using cache
CACHE_TTL_SECS = int(os.environ.get('CACHE_TTL_SECS')) # 900 = 15 mins

# Min wait in seconds between calls before making the request to CoinGecko
WAIT_BETWEEN_CALLS_SECS = int(os.environ.get('WAIT_BETWEEN_CALLS_SECS')) # 10 secs

# To queue requests sequentially to CoinGecko
cg_requests_lock = Lock()

# Timestamp of the previous call made by this instance
previous_call_ts = 0

# Default headers in response
headers = {
    'Content-Type': 'application/json'
}

@functions_framework.http
def market_summary(request):
    """HTTP Cloud Function.
    Args:
        request (flask.Request): The request object.
        <https://flask.palletsprojects.com/en/1.1.x/api/#incoming-request-data>
    Returns:
        The response text, or any set of values that can be turned into a
        Response object using `make_response`
        <https://flask.palletsprojects.com/en/1.1.x/api/#flask.make_response>.
    """
    global previous_call_ts, cg_requests_lock
    request_args = request.args
    if request_args and 'page' in request_args:
        page = request_args['page']
    else:
        page = '1'
    # The URL to send the request to
    url = 'https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&sparkline=false&page='+page
    LOG_PAGE_INFO = "[Page no " + page + "] "

    data = ""
    if url in response_cache_dict and (time.time() - response_cache_dict[url][1]) < CACHE_TTL_SECS :
        print(LOG_PAGE_INFO + "Request within rate limit tolerance period. So serving data from cache.")
        data, store_time = response_cache_dict[url]
    else:
        try:
            # Process the request only after the mandatory wait time since the previous call
            cg_requests_lock.acquire()
            current_time = time.time()
            if (current_time - previous_call_ts) < WAIT_BETWEEN_CALLS_SECS:
                sleep(previous_call_ts + WAIT_BETWEEN_CALLS_SECS - current_time)
            # Make the HTTP call and store the data in cache and record the time
            response = requests.get(url)
            response.raise_for_status()
            data = response.text
            previous_call_ts = time.time()
            response_cache_dict[url] = (data, previous_call_ts)
            cg_requests_lock.release()
            print(LOG_PAGE_INFO + "Retrieved data CoinGecko and added to cache.")
        except requests.HTTPError as exception:
            status_code = exception.response.status_code
            print(LOG_PAGE_INFO + "Received " + str(status_code) + " from CoinGecko. Attempting to serve data from cache if available.")
            if url not in response_cache_dict: # Very unlikely situation of service being re-initiated for this request and ALSO blocked by CoinGecko
                return ("Issue with coingecko, and data not in cache.", 500, {'Content-Type': 'text/text'})
            data, store_time = response_cache_dict[url]

    return (data, 200, headers)
