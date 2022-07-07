# nagios-argus-glue
Make use of the Obsess Feature in Nagios to use this glue-service.
Enable OSCP in nagios.cfg:

"obsess_over_services=1"
and
"ocsp_command=obsessive_service_handler"

Then defined a new command named obsessive_service_handler:

# obsessive_service_handler
define command {
  command_name obsessive_service_handler
  command_line /opt/Custom-Nagios-Plugins/nagios_argus_glue.py --description '$SERVICEDESC$ $SERVICEOUTPUT$' --hostname '$HOSTNAME$' --servicestateid '$SERVICESTATEID$' --lastservicestateid '$LASTSERVICESTATEID$' --lastproblemid '$LASTSERVICEPROBLEMID$' --problemid '$SERVICEPROBLEMID$' --notification '$SERVICENOTIFICATIONENABLED$' --notification_number '$SERVICENOTIFICATIONNUMBER$'
}
