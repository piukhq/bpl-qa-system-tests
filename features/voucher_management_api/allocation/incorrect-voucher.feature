# AC2: Rejected POST Request - Content - 400
#
#GIVEN I have a means of authorisation and the system is accessible
#
#WHEN I perform a POST operation against the “allocation” endpoint for an account holder
#
#AND the request is malformed (JSON decoder error)
#
#THEN I receive a 400 response with the below payload content;
#
#{
#  "display_message": "Malformed request.",
#  "error": "MALFORMED_REQUEST"
#}
