from twisted.python import usage
from twisted.application import strports


class Options(usage.Options):
    synopsis = "[-i <interface>] [-p <port>]"
    longdesc = "Makes a XMPP Server."
    optParameters = [
         ["interface", "i", "", "local interface to which we listen"],
         ["port", "p", "tcp:5222", "Port on which to listen"],



def makeService(config):



    port = config['port']
    if config['interface']:
        # Add warning here
        port += ':interface='+config['interface']
    return strports.service(port, t)


