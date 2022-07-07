#!/usr/bin/python3
import sys
import getopt

from pyargus.client import Client
from pyargus.models import Incident
from datetime import datetime

from config import config_token

#INPUT ARGUMENT
#nagios_argus_glue.py service

#Example
#python3 nagios_argus_glue.py --description NoPreDinnerSnackDetected --hostname feed.me.now --lastproblemid 0 --servicestateid 2 --problemid 1234 --lastservicestateid 0 --notification YES --notification_number 0

def myfunc(argv,config_token):
    arg_input = ""
    arg_output = ""
    arg_user = ""
    arg_servicestateid=0
    arg_lastservicestateid=0
    debug=0
    arg_help = "{0} -d <description> --hostname <hostname> -s --servicestateid <id> --lastservicestateid <id> --lastproblemid <id> --problemid <id> --test --notification <id> --notification_number <#>".format(argv[0])

    try:
        opts, args = getopt.getopt(argv[1:], "hi:u:o:", ["help", "description=","hostname=", "servicestateid=", "lastservicestateid=", "lastproblemid=", "problemid=", "notification=", "notification_number=","test"])
    except:
        print(arg_help)
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("--help"):
            print(arg_help)  # print the help message
            sys.exit(2)
        elif opt in ("-H", "--hostname"):
            arg_hostname = arg
        elif opt in ("-d", "--description"):
            arg_description = arg
        elif opt in ("-s", "--servicestateid"):
            arg_servicestateid = arg
        elif opt in ("-l", "--lastproblemid"):
            arg_lastproblemid = arg
        elif opt in ("-p", "--problemid"):
            arg_problemid = arg
        elif opt in ("--test"):
            debug=1
        elif opt in ("--sourceid"):
            arg_sourceid = arg
        elif opt in ("--lastservicestateid"):
            arg_lastservicestateid = arg
        elif opt in ("--notification"):
            arg_notification = arg
        elif opt in ("--notification_number"):
            arg_notification_number = arg


    #Debug purpose
    if debug==1:
        print('description:', arg_description)
        print('hostname:', arg_hostname)
        print('servicestateid:', arg_servicestateid)
        print('lastservicestateid:', arg_lastservicestateid)
        print('problemid:', arg_problemid)
        print('lastproblemid:', arg_lastproblemid)


    # Create logic for Info,Warning,Critical
    #This will set the <level 1-5> to be sent to Argus
    #5=Information
    #4=Low
    #3=Moderate
    #2=High
    #1=Critical

    # Create logic and set i.level= X #X= suitable level in argus according to above
    if (int(arg_servicestateid)==1):
        argus_level=3
    elif (int(arg_servicestateid)==2):
        argus_level=2
    else:
        argus_level=4


    #Description of macros in nagios
    #https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/3/en/macrolist.html#hoststatetype

    #If Notification are disabled for the Service - EXIT Follows $SERVICENOTIFICATIONENABLED$
    if (arg_notification == "NO" ):
        sys.exit(0)

    # Create incident with argus
    # Conditions for new Incident - Service StateID different from Last ServiceStateID, Last ServiceStateID is 0 and ProblemID is 0

    #First check ServiceID value
    if(int(arg_servicestateid)==0):
        #Check for state change
        if(int(arg_servicestateid)==int(arg_lastservicestateid)):
            #No state change - exit
            sys.exit(0)
        else:
            #State changed - clear case i Argus
            print('Clear incident')
            print(argv)
            #Initiate argus-client object
            c = Client(api_root_url="https://argus.cnaas.sunet.se:9000/api/v1", token=config_token)
            #Loop through incidents and match with problem id for source assigned in the Token
            for incident in c.get_my_incidents(open=True):
                if debug==1:
                    print(incident.source_incident_id)
                if(incident.source_incident_id==arg_problemid):
                    print("identical problem IDs")
                    print(incident.pk)
                    if debug==1:
                        print("TEST FLAG DETECTED - nothing sent to argus")
                    else:
                        print("PRODUCTION - sending to argus")
                        c.resolve_incident(incident=incident.pk, description=arg_hostname+'-'+arg_description[0:115], timestamp=datetime.now())
                        sys.exit(0)
    elif (int(arg_servicestateid)>0):
        #Check Notification-Number, create ticket on first notification, exit otherwise
        if(int(arg_notification_number)==0 or int(arg_notification_number)>1):
            sys.exit(0)
        elif (int(arg_notification_number)==1):
            print('create incident')
            print(argv)
            #Initiate argus-client object
            c = Client(api_root_url="https://argus.cnaas.sunet.se:9000/api/v1", token=config_token)
            i = Incident(
                description=arg_hostname+'-'+arg_description[0:115], #Merge hostname + description for better visibility in argus - truncate for SMS optimization
                start_time=datetime.now(),
                source_incident_id=arg_problemid,
                level=argus_level, #TODO: enhance logic for this (defined above)
                tags={
                    "host" : arg_hostname
                }
            )
            if debug==1:
                print("TEST FLAG DETECTED - nothing sent to argus")
                print(argus_level)
            else:
                print("PRODUCTION - sending to argus")
                output = c.post_incident(i)


if __name__ == "__main__":
    myfunc(sys.argv,config_token)
