from twisted.internet import protocol, defer
from twisted.words.xish import domish

from twisted.xmpp.namespaces import *
from twisted.xmpp.utils import PatternDispatcher, MatchString, MatchObject, MatchDict


class ProtocolReset(Exception):
    pass


class BaseProtocol(protocol.Protocol):

    def reset(self):
        raise NotImplementedError


    def connectionMade(self):
        self.listeners = []

        self.stream = domish.elementStream()

        self.stream.DocumentStartEvent = self.onDocumentStart
        self.stream.ElementEvent = self.onElement
        self.stream.DocumentEndEvent = self.onDocumentEnd

        self.onConnect()
        self.iq_count = 0


    def dataReceived(self, data):
        self.stream.parse(data)


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


    def onElement(self, elem):
        for matcher, listener in self.listeners:
            if matcher == elem:
                listener(elem)
                break

        

    def addElementListener(self, matcher, listener):
        self.listeners.append((matcher, listener))


    def removeElementListener(self, matcher, listener):
        self.listeners.remove((matcher, listener))


    def waitElement(self, matcher):
        d = defer.Deferred()
        def listener(elem):
            self.removeElementListener(matcher, listener)
            d.callback(elem)

        self.addElementListener(matcher, listener)
        return d


    handleIq = PatternDispatcher('handleIq')


    @handleIq.match
    def handleResultIq(self, result=MatchObject(attributes=MatchDict(type='result'))):
        return result.firstChildElement()


    @handleIq.match
    def handleErrorIq(self, result=MatchObject(attributes=MatchDict(type='error'))):
        raise result.firstChildElement()


    def sendIq(self, type, element):
        self.iq_count += 1
        iq = str(self.iq_count)

        e = domish.Element((NS_JABBER_CLIENT, 'iq'))
        e['type'] = type
        e['id'] = iq
        e.addChild(element)
        self.send(e)

        d = self.waitElement(
            MatchObject(
                name = 'iq',
                attributes = MatchDict(
                    type = MatchString('result')|MatchString('error'),
                    id = iq)))

        d.addCallback(self.handleIq)
        return d



