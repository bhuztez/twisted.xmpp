from twisted.internet import protocol
from twisted.words.protocols.jabber.jid import JID

from twisted.xmpp.namespaces import *
from twisted.xmpp.protocols import BaseProtocol, Stanza
from twisted.xmpp.utils import match, MatchInstance


class XmppEvent(object):
    pass


class XmppStreamInitiate(XmppEvent):
    pass


class StreamError(Exception):
    pass



class ServerProtocol(BaseProtocol):

    def onConnect(self):
        pass


    def onDocumentStart(self, root):
        self.domain = root['to']

        e = Stanza(
            (NS_STREAMS, 'stream'),
            NS_JABBER_CLIENT,
            { 'from': self.domain,
              'version': '1.0',
              'id': '%x'%(id(self)) },
            {'stream': NS_STREAMS})

        self.send(e, close=False)

        try:
            self.factory.router.route(self, JID(self.domain), XmppStreamInitiate)
        except StreamError, error:
            e = Stanza((NS_STREAM, 'error'))
            e.addElement(error.message, NS_XMPP_STREAMS)
            self.send(e)
            self.closeStream()



class Component(object):
    

    @match
    def handle(self,
               from_ = MatchInstance(ServerProtocol),
               to = MatchInstance(JID, user=None, resource=None),
               stanza_or_event = XmppStreamInitiate):
        pass



class Router(dict):

    @match
    def route(self,
              from_=MatchInstance(ServerProtocol),
              to=MatchInstance(JID, user=None, resource=None),
              stanza_or_event=XmppStreamInitiate):

        if to.host not in self:
            raise StreamError("host-unknown")

        self[to.host].handle(from_, to, stanza_or_event)


    def __setitem__(self, key, value):
        super(Router, self).__setitem__(key, value)
        value.router = self



class ServerFactory(protocol.ServerFactory):

    protocol = ServerProtocol


    def __init__(self, router):
        self.router = router


    # def buildProtocol(self, addr):
    #     pass







