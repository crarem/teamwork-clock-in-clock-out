#!/user/bin/env python

import RPi.GPIO as GPIO
import time
import requests
from requests.auth import HTTPBasicAuth
import datetime
from datetime import timedelta
from time import strptime
import json
from requestsRetry import robustRequest

def clockedDuration():

    twUrl = 'https://<subdomain>.teamwork.com/people/189608/clockins.json'            #Setting the TW URL endpoint for retrieving all user clockins
    un = '<username>'						                                          #TW API username and password
    pw = '<pw>'
    headers = {'content-length':'0'}                                                 #setting headers necessary for requests to run

    today = datetime.datetime.today() + timedelta(hours=13)                          #pulling today's UTC date + NZ 13 hours offset
    today_trunc = today.strftime('%y-%m-%d')                                         #transforming the date to today's y-m-d format
    now = today.strftime('%Y-%m-%d %H:%M:%S')                                        #taking the exact time right now in y-m-d H-M-S format

    try:
        #r3 = requests.get(twUrl,headers=headers,auth=HTTPBasicAuth(un,pw))                                     #sending POST request to bring in all user clockin logs
        r3 = robustRequest().get(twUrl,headers=headers,auth=HTTPBasicAuth(un,pw),verify=False, timeout=5)
    except Exception as e:                                                           #capturing exceptions so script doesn't break
        print ("TW duration check retrieval failed", e.__class__.__name__)
        print (e)
        while True:                                                                  #flashing LEDs on buttons with 1s intervals to signal error
            GPIO.output(40,GPIO.HIGH)
            GPIO.output(38,GPIO.HIGH)
            time.sleep(1)
            GPIO.output(40,GPIO.LOW)
            GPIO.output(38,GPIO.LOW)
            time.sleep(1)
            if GPIO.input(11)==False or GPIO.input(35)==False:                       #if an error occurs, the user can press a button to reset the system
                print ("resetting system")
                break
    else:
        response = json.loads(r3.text)
        numClocked = len(response["clockIns"])

    #print(response['clockIns'][0]['clockInDatetime'])

    clockins_raw = []                                                                #setting empty arrays for use in loops below to calculate durations
    clockins_offset = []
    clockouts_raw = []
    clockouts_offset = []

    for x in range(0, numClocked-1):                                                 #looping for length of clockins array

        ci = str(response['clockIns'][x]['clockInDatetime']).replace('T',' ')[:-1]             #retrieving each clockin date and time and stripping out some characters
        ci_os = datetime.datetime.strptime(ci, '%Y-%m-%d %H:%M:%S') + timedelta(hours=13)      #setting clockin offset with +13 hours for NZ local time

        co = str(response['clockIns'][x]['clockOutDatetime']).replace('T',' ')[:-1]            #retrieving each clockout date and time and stripping out some characters
        if co=='':                                                                             #handling the instance when a clock out entry isn't present (user still clocked in)
            co_os= datetime.datetime.strptime(now, '%Y-%m-%d %H:%M:%S')                        #setting this empty value to the current time for duration calculations
        else:
            co_os = datetime.datetime.strptime(co, '%Y-%m-%d %H:%M:%S') + timedelta(hours=13)  #setting clockout offset +13 hours for NZ local time

        if str(today_trunc) in ci:                                                             #checking if today's date within the ci value for today's duration calculation
            clockins_raw.append(ci)                                                            #appending to the clockin arrays the raw and offset clockin values
            clockins_offset.append(ci_os)
            clockouts_raw.append(co)                                                           #appending to the clockout arrays the raw and offset clockout values
            clockouts_offset.append(co_os)

    durations = [a-b for a, b in zip(clockouts_offset, clockins_offset)]                       #returning all the differences between each clockout and clockin time for today in durations array

    if len(durations)==0:                                                                      #handling the case when there have been no clockins or clockouts for the day
        total = 0
    else:
        total = durations[0]                                                                   #initialising the total variable starting with the first durations value
        for i in range(1,len(durations)-1):                                                    #looping through all durations values starting with the second one
            total = total + durations[i]                                                       #adding each new durations value to the total

    return total                                                                               #returning the total to the function request
