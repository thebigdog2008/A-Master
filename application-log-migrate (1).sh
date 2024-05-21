#!/bin/bash

##############################
#####  Log BACKUP Script #####
##############################

# Switch to Log folder

Now=$(date "+%Y-%m-%d")
Service=Service-Logs-$Now.zip
Listhub=Listhub-Logs-$Now.zip
Common=Common-Logs-$Now.zip
echo $Now

#Switch the folder to fatzoo folder

cd ~/realtorx/

#Moving General service Logs to the S3 bucket
 
sudo zip -r $Service logs/
 
aws s3 mv $Service s3://agentloop-server-logs/Agentloop-Dev/

#Moving General service Logs to the S3 bucket
 
sudo zip -r $Listhub list_hub/
 
aws s3 mv $Listhub s3://agentloop-server-logs/Agentloop-Dev/

#Application folder logs migarted to s3 bucket(400_errors.log,500_errors.log,debug.log,push_reminder.log)
 
sudo zip -r $Common *.log
 
aws s3 mv $Common s3://agentloop-server-logs/Agentloop-Dev/
