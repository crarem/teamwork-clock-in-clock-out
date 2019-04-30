# Teamwork Projects Clock-in, Clock-out Push Button Device
Python scripts for creating a desktop push button device to clock in and out of work.

This project was made to create an easy way for myself and my team to clock in and out of our teamwork.com projects using physical buttons sitting on our desks.

The device I created had two buttons with inbuilt LED rings (one red and one green).

When clocked in, the red, clock out button lights up and vice versa when clocked out.

The user is automatically clocked out at midnight, in case they forget to do so when they leave the office.

The driver for creating it was that currently in teamwork you have to navigate to the website portal to manage your clockins and this created extra friction which may lead to inaccurate tracking. Having easy to access, lit up buttons on your desk was a much more visible and easy way to interact with the clockins system.

There is also functionality built into these scripts to return the current amount of time you have been clocked in for the day. In the device I made, I have not included a method for displaying this at this stage as it added extra cost.

You can set the time interval for how often you want the device to check with the teamwork servers the clocked in status of the user. This is because the user may clock in via the teamwork software interface rather than the device so they need to sync up. So as not to overload the Teamwork servers, I set this to 60s.

The core file is clockInClockOut.py, run this in the same directory as the other files and make sure to enter your personal teamwork projects credentials within the script.

clockedStatus.py is a script which syncs the device with the user's clocked in status as per the Teamwork server. This is in case the user clocks in/out via the web portal instead of the device.

clockedDuration.py returns the amount of clocked in time the user has recorded today.

requestsRetry.py is a script that has all the configuration settings for making requests to the teamwork server, handling errors and retrying if there are any connection issues.
