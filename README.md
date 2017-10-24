# qreplication-manager

A script to start new replication jobs on Qumulo clusters and provide feedback on status of jobs via email to administrator. 

qreplication --sourcehost=host.example.com --targethost=host2.example.com --sourcepath=/path/to/source --targetpath=/path/to/target

Configure smtp settings and login information for source cluster in qconfig.json file. An example file is included. 
