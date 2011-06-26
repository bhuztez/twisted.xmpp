from twisted.internet import protocol, defer
from twisted.words.xish import domish

from twisted.xmpp.namespaces import *
from twisted.xmpp.utils import PatternDispatcher, MatchString, MatchInstance, MatchDict


Stanza = domish.Element


class ProtocolReset(Exception):
    pass


class BaseProtocol(protocol.Protocol):

    def reset(self):
        raise NotImplementedError


    def connectionMade(self):
        self.listeners = []

        self.stream = domish.elementStream()

        self.stream.DocumentStartEvent = self.onDocumentStart
        self.stream.ElementEvent = self.onStanzaOrEvent
        self.stream.DocumentEndEvent = self.onDocumentEnd

        self.onConnect()
        self.iq_count = 0


    def dataReceived(self, data):
        try:
            self.stream.parse(data)
        except domish.ParserError:
            e = Stanza((NS_STREAMS, 'error'))
            e.addElement('bad-format', NS_XMPP_STREAMS)
            self.send(e)
            self.closeStream()


    def send(self, element, close=True, defaultUri=None):
        s = domish.SerializerClass()
        s.serialize(
            element,
            closeElement=close,
            defaultUri=(defaultUri or NS_JABBER_CLIENT) if close else defaultUri)

        self.transport.write(s.getValue().encode('utf-8'))


    def closeStream(self):
        self.transport.write('</stream:stream>')
        self.transport.loseConnection()


    def onDocumentStart(self, root):
        raise NotImplementedError


    def onDocumentEnd(self):
        raise NotImplementedError


    def onStanzaOrEvent(self, stanza_or_event):
        for matcher, listener in self.listeners:
            if matcher == stanza_or_event:
                listener(stanza_or_event)

        

    def addListener(self, matcher, listener):
        self.listeners.append((matcher, listener))


    def removeListener(self, matcher, listener):
        self.listeners.remove((matcher, listener))


    def waitStanzaOrEvent(self, matcher):
        d = defer.Deferred()
        def listener(stanza_or_event):
            self.removeListener(matcher, listener)
            d.callback(stanza_or_event)

        self.addListener(matcher, listener)
        return d


    handleIq = PatternDispatcher('handleIq')


    @handleIq.match
    def handleResultIq(self, result=MatchInstance(Stanza, attributes=MatchDict(type='result'))):
        return result.firstChildElement()


    @handleIq.match
    def handleErrorIq(self, result=MatchInstance(Stanza, attributes=MatchDict(type='error'))):
        raise result.firstChildElement()


    def sendIq(self, type, element):
        self.iq_count += 1
        iq = str(self.iq_count)

        e = Stanza((NS_JABBER_CLIENT, 'iq'))
        e['type'] = type
        e['id'] = iq
        e.addChild(element)
        self.send(e)

        d = self.waitStanzaOrEvent(
            MatchInstance(Stanza,
                name = 'iq',
                attributes = MatchDict(
                    type = MatchString('result')|MatchString('error'),
                    id = iq)))

        d.addCallback(self.handleIq)
        return d



