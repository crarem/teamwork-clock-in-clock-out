#!/user/bin/env python

import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import json

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)  #turn off SSL warnings

def robustRequest(
    retries = 5,                                 #set number of times to retry the request after failure
    backoff_factor = 1,                          #algorithmic factor for growing time between retries
    status_forcelist=(500,502,504),              #the HTTP responses to force a failure on
    session=None,
):
    session = session or requests.Session()
    retry = Retry(  
        total = retries,                         #setting the parameters for the urllib3 requests function
        read = retries,
        connect = retries,
        backoff_factor = backoff_factor,
        status_forcelist = status_forcelist
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://',adapter)
    session.mount('https://',adapter)            #specifying for which types of URLs to use this function - http/https covers all URLs
    return session
