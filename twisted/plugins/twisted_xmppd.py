from twisted.application.service import ServiceMaker

TwistedXmppd = ServiceMaker(
    "Twisted XMPP Server",
    "twisted.xmpp.tap",
    "Twisted XMPP Server",
    "xmppd")

