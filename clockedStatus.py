#!/user/bin/env python

import RPi.GPIO as GPIO
import time
import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import datetime
from datetime import timedelta
from time import strptime
import json
from requestsRetry import robustRequest

def clockedStatus():

    twUrl = 'https://<subdomain>.teamwork.com/people/189608/clockins.json'   #specifying url for returning all clockins
    un = '<username>'						                                 #specifying username
    pw = '<pw>'                                                             #specifying teamwork password
    headers = {'content-length':'0'}                                        #setting minimum headers (necessary for requests to work)

    today = datetime.datetime.today() + timedelta(hours=13)                 #Setting NZ time for today for reference against clockins list
    today_trunc = today.strftime('%y-%m-%d')                                #truncating the result to just be year month and day

    t0 = time.time()                                                        #setting initial time for reference to calculate request duration

    try:
        #r3 = requests.get(twUrl,headers=headers,auth=HTTPBasicAuth(un,pw))
        r3 = robustRequest().get(twUrl,headers=headers,auth=HTTPBasicAuth(un,pw),verify=False, timeout=5)     #requesting using GET urllib3 function robustRequest with retries
    except Exception as e:                                                                                    #catching exceptions so that script doesn't end
        print ()"TW Status Check failed", e.__class__.__name__)                                                 #printing that request failure occurred and specifying the error
        print (e)
        r3 = None                                                                                             #r3 would not have been set if error so setting it to None to prevent breaking later
        while True:                                                                                           #while loop to flash button LEDs when error occurs so user knows
            GPIO.output(40,GPIO.HIGH)
            GPIO.output(38,GPIO.HIGH)
            time.sleep(1)
            GPIO.output(40,GPIO.LOW)
            GPIO.output(38,GPIO.LOW)
            time.sleep(1)
            if GPIO.input(11)==False or GPIO.input(35)==False:                                                #if an error occurs, the user can press a button to reset the system
                print ("resetting system")
                break                                                                                         #if a button is pressed the while loop breaks and function continues
    else:
        t1=time.time()                                                                                        #if the request is successful and r3 is set we print that it suceeded and the time taken
        print ()"Clock in status checked", t1-t0, "seconds", r3.status_code)


    if r3!=None:                                                                                              #checks to see if r3 properly set, i.e. no exception error in request
        response = json.loads(r3.text)                                                                        #sets json response of the request to the variable response
        numClocked = len(response["clockIns"])                                                                #counts the number of clockins items in the clockins array for the user

        clockins_offset = []                                                                                  #sets empty arrays for use later when transforming to local NZ time
        clockouts_offset = []

        for x in range(0, numClocked-1):                                                                      #for loop that is the same length as the clockins array

            ci = str(response['clockIns'][x]['clockInDatetime']).replace('T',' ')[:-1]                        #finds all clockin dates and times and removes some characters
            ci_os = datetime.datetime.strptime(ci, '%Y-%m-%d %H:%M:%S') + timedelta(hours=13)                 #offsets for local NZ time UTC+13


            co = str(response['clockIns'][x]['clockOutDatetime']).replace('T',' ')[:-1]                       #finds all clockout dates and times and removes some characters
            if co=='':                                                                                        #handles the case where the user has not clocked out yet
                co_os= ''                                                                                     #sets the offset value for the no clockouts case
            else:
                co_os = datetime.datetime.strptime(co, '%Y-%m-%d %H:%M:%S') + timedelta(hours=13)             #if there are clockout items, offset for local NZ time UTC+13

            if str(today_trunc) in ci:                                                                        #looks to check if clockin/clockout items are from today's date, not yesterday etc.
                clockins_offset.append(ci_os)                                                                 #adds to clockins and clockouts offset arrays if from today
                clockouts_offset.append(co_os)


        if len(clockouts_offset)==0:                                                                          #handles the case when there are no clockin or clockout items so user clockedout
            status='0'                                                                                        #set status to 0 for clocked out
        elif clockouts_offset[0]=='':                                                                         #if the first item of clockouts is empty, then user must be clockedin
            status='1'                                                                                        #set status to 1 for clocked in
        else:
            status='0'                                                                                        #otherwise user is clocked out and set status to 0

    else:
        status='0'

    return status
