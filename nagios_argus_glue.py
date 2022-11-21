#!/usr/bin/python3
import sys
import getopt
import os

from pyargus.client import Client
from pyargus.models import Incident
from datetime import datetime

from config import config_token

# INPUT ARGUMENT
# Example
# nagios_argus_glue.py --description 'Swap Usage SWAP CRITICAL - 0% free (0 M out of 0 MB) - Swap is either disabled, not present, or of zero size. --hostname 'localhost' --servicestateid '2' --lastservicestateid '2' --lastproblemid '1373' --problemid '1374' --notification 'YES' --notification_number '502'

debug = 0
validate = 0


def createIncident(config_token, problemid, hostname, description, level):
    # Create child process to notify ARGUS and  release nagios-check (parent) process
    fork_pid = os.fork()
    if fork_pid == 0:
        # Initiate argus-client object TODO read api_root_url from config file
        c = Client(api_root_url="https://argus.cnaas.sunet.se:9000/api/v1", token=config_token)
        i = Incident(
            description=hostname+'-'+description[0:115],  # Merge hostname + trunked description for better visibility in argus
            start_time=datetime.now(),
            source_incident_id=problemid,
            level=level,  # TODO make logic for this (now 1-1 translation from nagios to argus)
            tags={
                "host": hostname
            }
        )
        log(debug, "---- END --- Argus will take it from here")
        if validate == 1:
            log(debug, "(VALIDATE FLAG DETECTED - create notification not  sent to argus)")
            sys.exit(0)
        else:
            output = c.post_incident(i)
            log(print, output)
        sys.exit(0)
    # Terminate nagios-check (parent) process
    elif fork_pid > 0:
        log(debug, "---- END --- PID is out, descendant takes over")
        sys.exit(0)
    else:
        log(debug, "Sorry!! Child Process creation has failed...")
        sys.exit(2)


def closeIncident(config_token, problemid, lastproblemid, hostname, close_description):
    # State changed - clear case i Argus
    log(debug, 'Clear incident')
    # Create child process to notify ARGUS and  release nagios-check (parent) process
    fork_pid = os.fork()
    log(debug, 'PID {}'.format(fork_pid))
    if fork_pid == 0:
        # Initiate argus-client object TODO read api_root_url from config file
        c = Client(api_root_url="https://argus.cnaas.sunet.se:9000/api/v1", token=config_token)
        # Loop through incidents on Argus
        for incident in c.get_my_incidents(open=True):
            log(debug, incident.source_incident_id)
            # Service recovery notification still contains the problemId in the problemID variable, Hosts however move it over to lastproblemID
            if(incident.source_incident_id in (problemid, lastproblemid)):
                log(debug, incident.pk)
                log(debug, "---- END --- Argus will take it from here")
                if validate == 1:
                    log(debug, incident.pk)
                    log(debug, "(VALIDATE FLAG DETECTED - clear notification not sent to argus)")
                    sys.exit(0)
                else:
                    c.resolve_incident(incident=incident.pk, description=hostname+'-'+close_description[0:115], timestamp=datetime.now())
                sys.exit(0)
        log(debug, "---- END --- No matching incidents found")
        sys.exit(0)
    # Terminate nagios-check (parent) process
    elif fork_pid > 0:
        log(debug, "---- END --- PID is out, descendant takes over")
        sys.exit(0)
    else:
        log(debug, "Sorry!! Child Process creation has failed...")
        sys.exit(2)


def log(log_level, message):
    if log_level == 1:
        print(message)


def myfunc(argv, config_token):
    arg_servicestateid = 0
    arg_lastservicestateid = 0
    sync = 0
    test_api = 0
    arg_help = ("{0} -d <description> --hostname <hostname> -s --servicestateid <id> --lastservicestateid <id> --lastproblemid <id> --problemid <id> --test --notification <id> --notification_number <#>".format(argv[0]))

    try:
        opts, args = getopt.getopt(argv[1:], "hi:u:o:", ["help", "description=", "hostname=", "servicestateid=", "lastservicestateid=", "lastproblemid=", "problemid=", "notification=", "notification_number=", "debug", "sync", "test-api", "validate"])
    except any:
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
            arg_servicestateid = int(arg)
        elif opt in ("-l", "--lastproblemid"):
            arg_lastproblemid = arg
        elif opt in ("-p", "--problemid"):
            arg_problemid = arg
        elif opt in ("--lastservicestateid"):
            arg_lastservicestateid = int(arg)
        elif opt in ("--notification"):
            arg_notification = arg
        elif opt in ("--notification_number"):
            arg_notification_number = int(arg)
        elif opt in ("--test-api"):
            test_api = 1
        elif opt in ("--debug"):
            global debug
            debug = 1
        elif opt in ("--sync"):
            sync = 1
        elif opt in ("--validate"):
            global validate
            validate = 1

    if test_api == 1:
        try:
            client = Client(api_root_url="https://argus.cnaas.sunet.se:9000/api/v1", token=config_token)
            incidents = client.get_incidents(open=True)
            next(incidents, None)
            print(
                "Argus API is accessible at {}".format(client.api.api_root_url), file=sys.stderr
                )
        except any:
            print(
                "ERROR: Argus API failed on {}".format(client.api.api_root_url), file=sys.stderr
                )
            sys.exit(2)
        sys.exit(0)

    # Debug purpose
    log(debug, "---- START ---")
    log(debug, 'description: {}'.format(arg_description))
    log(debug, 'hostname: {}'.format(arg_hostname))
    log(debug, 'servicestateid: {}'.format(arg_servicestateid))
    log(debug, 'lastservicestateid: {}'.format(arg_lastservicestateid))
    log(debug, 'problemid: {}'.format(arg_problemid))
    log(debug, 'lastproblemid: {}'.format(arg_lastproblemid))
    log(debug, 'notification: {}'.format(arg_notification))
    log(debug, 'notification_number: {}'.format(arg_notification_number))

    # TODO find a way to syncronize argus and nagios
    if sync == 1:
        log(debug, "---- END --- SYNC Funtion not yet in place")
        sys.exit(0)

    # TODO Create logic for Info,Warning,Critical
    # This will set the <level 1-5> to be sent to Argus
    # 5=Information
    # 4=Low
    # 3=Moderate
    # 2=High
    # 1=Critical

    # Create logic and set i.level= X #X= suitable level in argus according to above
    argus_level = 4

    # Description of macros in nagios
    # https://assets.nagios.com/downloads/nagioscore/docs/nagioscore/4/en/macrolist.html

    # If Notification are disabled for the Service - EXIT Follows $SERVICENOTIFICATIONENABLED$
    if arg_notification == "NO":
        log(debug, "---- END --- No notification on this check")
        sys.exit(0)

    # Create incident with argus
    # Conditions for new Incident - Service StateID different from Last ServiceStateID, Last ServiceStateID is 0 and ProblemID is 0

    # First check ServiceID value
    if arg_servicestateid == 0:
        # Check for state change
        if arg_servicestateid == arg_lastservicestateid:
            # No state change - exit
            log(debug, "---- END --- Check is still green")
            sys.exit(0)
        else:
            closeIncident(config_token=config_token, problemid=arg_problemid, lastproblemid=arg_lastproblemid, hostname=arg_hostname, close_description=arg_description)
    elif arg_servicestateid > 0:
        # Check Notification-Number, create ticket on first notification,
        # exit otherwise
        if (arg_notification_number == 0 or arg_notification_number > 1):
            log(debug, "---- END --- Argus is already aware of this issue")
            sys.exit(0)
        elif arg_notification_number == 1:
            createIncident(config_token, arg_problemid, arg_hostname, arg_description, argus_level)
        else:
            sys.exit(0)


if __name__ == "__main__":
    myfunc(sys.argv, config_token)
