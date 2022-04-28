# AWS_Automation
Python 3 program to automate the process of  creating, launching and monitoring public-facing web servers in the Amazon cloud. 

# The Script does the following

## 1) Launch an EC2 instance
Launches a new Amazon EC2 nano instance using Boto3 APO library.

## 2) Configure appropriate instance settings
Launches the instance into an appropriate security group, instance is tagged and is accessible using your SSH key.

## 3) Set up S3 website
Provide a “User Data” script when creating the instance.
Configure the web server index page to display instance metadata (e.g. availability zone, private IP address, subnet)
Create an S3 bucket. This bucket contains two items:
o An dynamic image which we will make available at a URL.
o A web page called index.html which displays the image - e.g. using <img> tag

## 4) Launch browser and display both URLs.
Launchs a web browser and opens both EC2 and your S3 web pages

## 5) Monitoring
A bash script called monitor.sh that runs some sample terminal
commands that carry out monitoring
