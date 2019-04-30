#!/user/bin/env python

import RPi.GPIO as GPIO
import time
import requests
from requests.auth import HTTPBasicAuth
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import datetime
from datetime import timedelta
from clockedDuration import clockedDuration
from clockedStatus import clockedStatus
from requestsRetry import robustRequest

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(35, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(33, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(40,GPIO.OUT)
GPIO.setup(38,GPIO.OUT)

ciUrl = 'https://<subdomain>.teamwork.com/me/clockin.json'                                            #specifying teamwork clockin API endpoint 
coUrl = 'https://<subdomain>.teamwork.com/me/clockout.json'                                           #specifying teamwork clockout API endpoint
un = '<username>'                                                              						#specifying teamwork API username
pw = '<pw>'                                                                                          #specifying teamwork API password
headers = {'content-length':'0'}                                                                     #specifying minimum header for requests to work

clockInStatus = '1'                                                                                  #establishing clocked in status variable with a starting value of 1 (clocked in)
start = time.time()                                                                                  #initialising time counter to help with syncing clockin status with teamwork servers
    
while True:
      button1_input_state = GPIO.input(11)                                                           #setting clockin button variable
      button2_input_state = GPIO.input(35)                                                           #setting clockout button variable
      button3_input_state = GPIO.input(33)                                                           #setting time worked check button variable
      led_input1_state = GPIO.input(40)                                                              #setting red clockout LED variable
      led_input2_state = GPIO.input(38)                                                              #setting green clockin LED variable

      timestamp = datetime.datetime.today() + timedelta(hours=13)                                    #taking timestamp of current time and offsetting to NZ local time
      timestamp.strftime('%H-%M-%S')                                                                 #setting format of today's date

      elapsed = time.time()                                                                          #starting timer
      interval = round(elapsed-start,0)                                                              #calculating interval between start timer and time elapsed for use in syncing with teamwork
      

      if interval%60==0:                                                                             #checking if specified duration has past (60s)
            clockInStatusSync=clockedStatus()                                                        #referencing the clockInStatus function to check with teamwork what clockin status is
            if clockInStatusSync!=clockInStatus:                                                     #checking if the value stored locally is different to what teamwork has set
                  clockInStatus=clockInStatusSync                                                    #if the values are different, set our local status to what teamwork says
                  print('digital clocked status synced!')                                            #let the user know that a sync has occured changing the local clocked in status
                  print(clockInStatus)                                                               #print what the new status is
     
      elif (button1_input_state == True) and (button2_input_state==True) and (button3_input_state==True):   #if no buttons are being pressed (TRUE) then check the status and change LEDs accordingly
        if clockInStatus=='1':                                                                              #user clocked in, turn red light off and green light on
            GPIO.output(40,GPIO.LOW)
            GPIO.output(38,GPIO.HIGH)
        elif clockInStatus=='0':                                                                            #user clocked out, turn red light off and green light on
            GPIO.output(40,GPIO.HIGH)
            GPIO.output(38,GPIO.LOW)
        
        time.sleep(0.1)
            
      elif (button1_input_state == False) and (clockInStatus=='0'):                                         #if user clicks green clock in button and user currently clocked out
        print('Clocked In!')                                                                                #print that the user is clocking in
        GPIO.output(40,GPIO.LOW)                                                                            #switch the LEDs states around
        GPIO.output(38,GPIO.HIGH)

        try:                                                                                                
              r1 = requests.post(ciUrl,headers=headers,auth=HTTPBasicAuth(un,pw),verify=False, timeout=5)   #send a POST request to TW to clock the user in
        except Exception as e:                                                                              #handle any exceptions
              print e                                                                                       #let the user know what the exception was
              while True:                                                                                   #flash the button LEDs to let the user know an error has occurred
                    GPIO.output(40,GPIO.HIGH)
                    GPIO.output(38,GPIO.HIGH)
                    time.sleep(1)
                    GPIO.output(40,GPIO.LOW)
                    GPIO.output(38,GPIO.LOW)
                    time.sleep(1)
                    if GPIO.input(11)==False or GPIO.input(35)==False:                                      #if an error occurs, the user can press a button to reset the system
                        print "resetting system"
                        break
        else:
              print(r1.status_code)                                                                               #if the request is successful print a 201 status             
              if r1.status_code == 201:
                    clockInStatus = '1'                                                                             #if we get a 201 response, set the clockinstatus to 1
            
        time.sleep(0.1)

      elif (button1_input_state == False) and (clockInStatus=='1'):                                         #if user clicks to clock in but status already equals 1
        print('You are Already Clocked In!')                                                                #user is already clocked in and print this for feedback

        time.sleep(0.1)

      elif (button2_input_state == False) and (clockInStatus=='1'):                                         #same process as above but for clocking out, green LED on, Red LED off
        print('Clocked Out!')
        GPIO.output(40,GPIO.HIGH)
        GPIO.output(38,GPIO.LOW)

        try:
              r2 = robustRequest().post(coUrl,headers=headers,auth=HTTPBasicAuth(un,pw),verify=False, timeout=5)  #POST request sent to clockout API endpoint
        except Exception as e:
              print e
              while True:
                    GPIO.output(40,GPIO.HIGH)
                    GPIO.output(38,GPIO.HIGH)
                    time.sleep(1)
                    GPIO.output(40,GPIO.LOW)
                    GPIO.output(38,GPIO.LOW)
                    time.sleep(1)
                    if GPIO.input(11)==False or GPIO.input(35)==False:                                      #if an error occurs, the user can press a button to reset the system
                        print "resetting system"
                        break
        else:
              print(r2.status_code)
              if r2.status_code == 201:
                    clockInStatus = '0'

        time.sleep(0.1)

      elif (button2_input_state == False) and (clockInStatus=='0'):                                         #if user already clocked out and clockout pressed, feedback given
        print('You are Already Clocked Out!')

        time.sleep(0.1)

      elif button3_input_state == False:                                                                    #if user presses third button to check how much time logged today, run function
        hours = clockedDuration()
        print "You`ve been working for: ",hours," hours today"                                              #print feedback with hours returned from the clockedDuration function

        time.sleep(0.1)

      elif timestamp.strftime('%H-%M-%S') == '13-38-00':                                                    #if time strikes midnight, new day begins and user is automatically clocked out
        print('You have been automatically clocked out for the day!')
        GPIO.output(40,GPIO.HIGH)                                                                           #set red LED off and green LED on
        GPIO.output(38,GPIO.LOW)

        try:
              r2 = robustRequest().post(coUrl,headers=headers,auth=HTTPBasicAuth(un,pw),verify=False, timeout=5)  #run process for sending request to clockout API endpoint
        except Exception as e:
              print e
              while True:
                    GPIO.output(40,GPIO.HIGH)
                    GPIO.output(38,GPIO.HIGH)
                    time.sleep(1)
                    GPIO.output(40,GPIO.LOW)
                    GPIO.output(38,GPIO.LOW)
                    time.sleep(1)
                    if GPIO.input(11)==False or GPIO.input(35)==False:                                      #if an error occurs, the user can press a button to reset the system
                        print "resetting system"
                        break
        else:
              print(r2.status_code)
              if r2.status_code == 201:
                    clockInStatus = '0'

        time.sleep(0.5)
