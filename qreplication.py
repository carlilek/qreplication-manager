#!/usr/bin/env python

import os
import sys
import json
import smtplib
from email.mime.text import MIMEText
import argparse
from qumulo.rest_client import RestClient

### Edit the configpath for the location of your qconfig.json ### 
configpath = "/root/bin/reprunner/qconfig.json"
#################################################################

# Import qconfig.json for login information and other settings
def getconfig():
    configdict = {}
    try:
        with open (configpath, 'r') as j:
            config = json.load(j)
    
        configdict['sender'] = str(config['email settings']['sender_address'])
        configdict['smtp_server'] = str(config['email settings']['server'])
        configdict['recipient'] = str(config['email settings']['recipient'])
        configdict['host'] = str(config['qcluster']['url'])
        configdict['user'] = str(config['qcluster']['user'])
        configdict['password'] = str(config['qcluster']['password'])
        configdict['port'] = 8000
        configdict['logfile'] = str(config['output_log']['logfile'])
    
    except Exception, excpt:
        print "Improperly formatted {} or missing file: {}".format(configpath, excpt)
        sys.exit(1)

    return configdict

def login(configdict):
    '''Obtain credentials from the REST server'''
    try:
        rc = RestClient(configdict['host'], configdict['port'])
        rc.login(configdict['user'], configdict['password'])
    except Exception, excpt:
        print "Error connecting to the REST server: %s" % excpt
        print __doc__
        sys.exit(1)
    return rc

def send_mail(configdict, subject, body):
    try:
        mmsg = MIMEText(body, 'html')
        mmsg['Subject'] = subject
        mmsg['From'] = configdict['sender']
        mmsg['To'] = configdict['recipient']

        session = smtplib.SMTP(configdict['smtp_server'])
        session.sendmail(configdict['sender'], configdict['recipient'], mmsg.as_string())
        session.quit()
    except Exception,excpt:
        print excpt

def build_mail(repexcept, rep, relid, sourcehost, targethost, sourcepath, targetpath):
    status = rep.get_relationship_status(relid)
    print status
    subject = 'Replication status for {}:{}'.format(sourcehost,sourcepath)
    body = "Relationship ID: <br>"
    body += "{}<br><br>".format(relid)
    body += "Source: <br>" 
    body += "{}:{}<br><br>".format(sourcehost, sourcepath)
    body += "Target: <br>"
    body += "{}:{}<br><br>".format(targethost, targetpath)
    body += "Status: <br>"
    body += "{}<br><br>".format(status['job_state'])
    body += "Start Time: <br>"
    body += "{}<br><br>".format(status['start_time'])
    body += "Last End Time: <br>"
    body += "{}<br><br>".format(status['last_ended_time'])
    body += "Error from last job: <br>"
    body += "{}<br><br>".format(status['error_from_last_job'])

    body += "Exception (if any): <br>"
    body += "{}".format(repexcept)
    
    send_mail(configdict, subject, body)
     

def findrelationship(rep, sourcehost, targethost, sourcepath, targetpath):
    reprel = rep.list_relationships()['entries']
    for relationship in reprel:
        if relationship['source_cluster_name'] == sourcehost \
                and relationship['target_cluster_name'] == targethost \
                and relationship['source_path'] == sourcepath \
                and relationship['target_path'] == targetpath:
            return relationship['id']

def main(argv):
    global configdict
    configdict = getconfig()
    parser = argparse.ArgumentParser(description="Start a Qumulo replication")
    parser.add_argument("--sourcehost", type=str, required=True)
    parser.add_argument("--targethost", type=str, required=True)
    parser.add_argument("--sourcepath", type=str, required=True)
    parser.add_argument("--targetpath", type=str, required=True)
    args = parser.parse_args()

    arglist = (args.sourcehost, args.targethost, args.sourcepath, args.targetpath)

    rc = login(configdict)
    rep = rc.replication
    relid = findrelationship(rep, *arglist)
    try: 
        rep.replicate(relid)
        repexcept = None
    except Exception,excpt:
        repexcept = excpt
    build_mail(repexcept, rep, relid, *arglist)    

if __name__ == '__main__':
    main(sys.argv[1:])
