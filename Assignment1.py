#!/usr/bin/env python3
import sys
import boto3
import urllib.request
import json
import datetime
import os
import webbrowser
import time
import requests
import subprocess
from datetime import datetime, timedelta
import time

cloudwatch = boto3.resource('cloudwatch')
client = boto3.client('ec2')
s3_client = boto3.client("s3")
s3_resource = boto3.resource("s3")


## 1) Launch EC2 Instance
KEYNAME='JG07Mar2022'
SECURITYGROUP='sg-0be3fb54e80280591'
IMAGEID='ami-0c293f3f676ec4f90'


ec2 = boto3.resource('ec2')
instance = ec2.create_instances(
                                ImageId= IMAGEID,
                                MinCount=1,
                                MaxCount=1,
                                InstanceType='t2.nano',
                                KeyName=KEYNAME,                                         ## Allows SSH
                                SecurityGroupIds=[SECURITYGROUP],
                                UserData='''#!/bin/bash
                                yum update -y
                                yum install httpd -y
                                systemctl enable httpd
                                systemctl start httpd
                                echo "<html>" > index.html
                                echo "<hr>This instance is running in availability zone:" > index.html
                                curl http://169.254.169.254/latest/meta-data/placement/availability-zone >> index.html
                                echo "<hr>The instance ID is: " >> index.html
                                curl http://169.254.169.254/latest/meta-data/instance-id >> index.html
                                echo "<hr>The instance type is: " >> index.html
                                curl http://169.254.169.254/latest/meta-data/instance-type >> index.html
                                echo "<hr>The Private IP address is: " >> index.html
                                curl http://169.254.169.254/latest/meta-data/local-ipv4 >> index.html
                                cp index.html /var/www/html/index.html''',
                                TagSpecifications=[
                                    {
                                        'ResourceType': 'instance',
                                        'Tags': [
                                            {
                                                'Key': 'Assign1_Key',
                                                'Value': 'Assign1_MyWebServer',
                                            },
                                        ]
                                    },
                                ])
##instance[0].reload()                                       ## Reloadininstance before accessing properties
instance = instance[0]
INSTANCE_ID=instance.id
INSTANCE_STATE=instance.state
print (INSTANCE_ID, INSTANCE_STATE)
print ("Instance Initializing...")
instance.wait_until_running()
print("Instance Running")
instance.reload() 
IP_ADDRESS = instance.public_ip_address
print (IP_ADDRESS)
ec2_website_url = 'http://' + IP_ADDRESS
AvailabilityZone = instance.placement.get('AvailabilityZone') 

my_session = boto3.session.Session() ##https://stackoverflow.com/questions/37514810/how-to-get-the-region-of-the-current-user-from-boto
my_region = my_session.region_name
print(my_region)
print (ec2_website_url)

##############################################################################

image_url = 'http://devops.witdemo.net/assign1.jpg' #the image on the web
object_name = 'my_image.jpg' #local name to be saved
urllib.request.urlretrieve(image_url, object_name)

#############################################################################
print("...Creating Bucket ...")
bucket_name = 'bucket-' + datetime.now().strftime('%Y%m%d%H%M%S%f')
s3_webhost = 'http://' +  bucket_name + '.s3-website-' + my_region + '.amazonaws.com/'
print (bucket_name)
print (' S3 hosting URL -> ' + s3_webhost )
### Create Bucket
try:
    response = s3_resource.create_bucket(Bucket=bucket_name, ACL='public-read')
    print (response)
except Exception as error:
    print (error)

#### Put Image into Bucket
try:
    response = s3_resource.Object(bucket_name, object_name).put(Body=open(object_name, 'rb'), ACL='public-read', ContentType='image/jpeg')
    print (response)
except Exception as error:
    print (error)

#### List Buckets ACL='public-read'
##for bucket in s3_resource.buckets.all():
##    print (bucket.name)
##    print ("---")
##    for item in bucket.objects.all():
##        print ("\t%s" % item.key)

bucket_policy={
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicRead",
            "Effect": "Allow",
            "Principal": "*",
            "Action":[
                "s3:*"],
            "Resource": 
                [f"arn:aws:s3:::{bucket_name}/*", f"arn:aws:s3:::{bucket_name}"]
                
            
        }
    ]   
}
bucket_policy = json.dumps(bucket_policy)
s3_client.put_bucket_policy(Bucket=bucket_name,Policy=bucket_policy)

f=open("index.html", "w")
f.write("<html><head><title> WIT Assign1 </title></head><body><img src='my_image.jpg'> </body></html> ")
f.close
f.seek(0)

f2=open("error.html", "w")
f2.write("<html><body><h1>Something Went Wrong !!</h1></body></html>")
f2.close
f2.seek(0)

try:
    response = s3_resource.Bucket(bucket_name).upload_file('/home/compsys/2022/DevOps/Assignment1/index.html', 'index.html', ExtraArgs={'ContentType': 'text/html'})
    print (response)
except Exception as error:
    print (error)
try:
    response = s3_resource.Bucket(bucket_name).upload_file('/home/compsys/2022/DevOps/Assignment1/error.html', 'error.html', ExtraArgs={'ContentType': 'text/html'})
    print (response)
except Exception as error:
    print (error)

website_configuration = {
    'ErrorDocument': {'Key': 'error.html'},
    'IndexDocument': {'Suffix': 'index.html'},
}

##bucket_website = s3_resource.BucketWebsite(bucket_name)   # replace with your bucket name or a string variable
##response = bucket_website.put(WebsiteConfiguration=website_configuration)

s3_client.put_bucket_website(Bucket=bucket_name, WebsiteConfiguration=website_configuration)

##Step 5##
instance.reload() 
time.sleep(60)
webbrowser.open_new_tab(ec2_website_url)
time.sleep(2)
webbrowser.open_new_tab(s3_webhost)


###Step 6 - Monitoring ##
time.sleep(60)
cmd1 = 'scp -o StrictHostKeyChecking=no -i  ' + KEYNAME + '.pem monitor.sh ec2-user@' + IP_ADDRESS + ':.'
print ('cmd1 -> ' +  cmd1)
subprocess.run(cmd1, shell=True)
time.sleep(5)
cmd2 = 'ssh -o StrictHostKeyChecking=no -i  '+ KEYNAME + '.pem ec2-user@'+ IP_ADDRESS + " 'chmod 700 monitor.sh'"
print ('cmd2 -> ' +  cmd2)
subprocess.run(cmd2, shell=True)
time.sleep(5)
cmd3 = 'ssh -i '+ KEYNAME + '.pem ec2-user@'+ IP_ADDRESS + " './monitor.sh'"
print ('cmd3 -> ' + cmd3)
subprocess.run(cmd3, shell=True)

### Additional - Instance Metrics using CloudWatch ###
instance_ec2 = ec2.Instance(INSTANCE_ID)
instance_ec2.monitor()
time.sleep(360)
metric_iterator = cloudwatch.metrics.filter(Namespace='AWS/EC2',
                                            MetricName='CPUUtilization',
                                            Dimensions=[{'Name':'InstanceId', 'Value': INSTANCE_ID}])

metric = list(metric_iterator)[0]

reponse = metric.get_statistics(StartTime= datetime.utcnow() - timedelta(minutes=5),
                                EndTime=datetime.utcnow(),
                                Period=300,
                                Statistics=['Average'])

print("Average CPU Utilisation -> ", response['Datapoints'][0]['Average'], response['Datapoints'][0]['Units'])