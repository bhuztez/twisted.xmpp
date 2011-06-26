from twisted.internet import defer, protocol, ssl
from twisted.words.xish import domish

from twisted.xmpp.namespaces import *
from twisted.xmpp.protocols import BaseProtocol, ProtocolReset, Stanza
from twisted.xmpp.utils import PatternDispatcher, MatchInstance, NoMatchingClause


from base64 import b64decode, b64encode
import re, hashlib, random


class ClientMechanism(object):


    def __init__(self, proto):
        self.proto = proto


    @defer.inlineCallbacks
    def __call__(self):
        self.proto.sendSaslAuth(self.name, self.start())
        while True:
            status, data = yield self.proto.waitSasl()
            if status =='challenge':
                self.proto.sendSaslResponse(self.step(data))
            elif status == 'success':
                break
            elif status == 'failure':
                raise data
            else:
                raise Exception
            

    def start(self):
        raise NotImplementedError

    def step(self, data):
        raise NotImplementedError


class Plain(ClientMechanism):
    name = 'PLAIN'

    def start(self):
        return '\0%s\0%s'%self.proto.factory.credential


class DigestMD5(ClientMechanism):

    name = 'DIGEST-MD5'

    def start(self):
        self.challenge = self.digest
        return ''


    def step(self, data):
        args = [ ( match.group(1), match.group(2) )
                 for match in re.finditer(
                     r'(\w+)=([^,]+|(?:"(?:[^"]|\\")+(?<!\\)"))(?:,|$)', data) ]
        args = [ (k,v[1:-1].decode('string_escape')) if v.startswith('"') else (k,v)
                 for (k,v) in args ]

        return self.challenge(**dict(args))


    def digest(self, nonce, qop, **kwargs):
        assert qop == 'auth'
        nc="00000001"
        cnonce = hashlib.md5(str(random.randint(0,0x123456789ABCDEF0))).hexdigest()

        digest_uri = 'xmpp/' + self.domain
        h = hashlib.md5(':'.join([self.proto.credential[0], self.proto.domain, self.proto.credential[1]])).digest()
        a1 = hashlib.md5(':'.join([h, nonce, cnonce])).hexdigest()
        a2 = hashlib.md5('AUTHENTICATE:'+digest_uri).hexdigest()

        response = hashlib.md5(':'.join([a1, nonce, nc, cnonce, qop, a2])).hexdigest()

        a2 = hashlib.md5(':'+digest_uri).hexdigest()
        self.rspauth = hashlib.md5(':'.join([a1, nonce, nc, cnonce, qop, a2])).hexdigest()
        self.challenge = self.response

        return 'username="%s",realm="%s",nonce="%s",cnonce="%s",nc=%s,qop=%s,digest-uri="%s",response=%s,charset=utf-8'''%(
            self.proto.credential[0], self.proto.domain, nonce, cnonce, nc, qop, digest_uri, response)


    def response(self, rspauth, **kwargs):
        assert rspauth == self.rspauth
        return ''



	
MECHANISMS = [DigestMD5, Plain]




class ClientProtocol(BaseProtocol):


    def reset(self):
        self.connectionMade()
        raise ProtocolReset


    def onConnect(self):
        e = Stanza(
            (NS_STREAMS, 'stream'),
            NS_JABBER_CLIENT,
            { 'to': self.factory.domain,
              'version': '1.0' },
            {'stream': NS_STREAMS})

        self.send(e, False)


    @defer.inlineCallbacks
    def onDocumentStart(self, root):
        self.streamId = root['id']

        elem = yield self.waitStanzaOrEvent(
            MatchInstance(Stanza, uri=NS_STREAMS, name='features'))

        for feature in elem.children:
            try:
                yield self.handleStreamFeature(feature)
            except NoMatchingClause:
                pass


    handleStreamFeature = PatternDispatcher('handleStreamFeature')


    @handleStreamFeature.match
    def starttls(self, elem=MatchInstance(Stanza, uri=NS_XMPP_TLS, name='starttls')):
        uri = NS_XMPP_TLS
        self.send(Stanza((uri, 'starttls')))
        elem = yield self.waitStanzaOrEvent(MatchInstance(Stanza, uri=uri))
        if elem.name != 'proceed':
            raise Exception

        self.transport.startTLS(self.factory.ssl_ctx)
        self.reset()


    def select_mech(self, names):
        for mech in MECHANISMS:
            if mech.name in names:
                return mech(self)


    @handleStreamFeature.match
    def saslauth(self, elem=MatchInstance(Stanza, uri=NS_XMPP_SASL, name='mechanisms')):
        print [ mech.toXml() for mech in elem.children ]
        mech = self.select_mech([ mech.children[0] for mech in elem.children ])
        yield mech()
        self.reset()


    @handleStreamFeature.match
    def bind(self, elem=MatchInstance(Stanza, uri=NS_XMPP_BIND, name='bind')):
        e = Stanza((NS_XMPP_BIND, 'bind'))
        e.addElement('resource', content=self.factory.resource)
        elem = yield self.sendIq("set", e)
        elem = elem.firstChildElement()
        assert elem.name == 'jid'
        self.jid = elem.children[0]


    @handleStreamFeature.match
    def session(self, elem=MatchInstance(Stanza, uri=NS_XMPP_SESSION, name='session')):
        e = Stanza((NS_XMPP_SESSION, 'session'))
        elem = yield self.sendIq("set", e)


    handleStreamFeature = defer.inlineCallbacks(handleStreamFeature)


    def sendSaslAuth(self, mechanism, content=''):
        e = Stanza((NS_XMPP_SASL, 'auth'))
        e['mechanism'] = mechanism
        e.addContent(b64encode(content))
        self.send(e)



    def sendSaslResponse(self, content=''):
        e = Stanza((NS_XMPP_SASL, 'response'))
        e.addContent(b64encode(content))
        self.send(e)


    @defer.inlineCallbacks
    def waitSasl(self):
        elem = yield self.waitStanzaOrEvent(MatchInstance(Stanza, uri=NS_XMPP_SASL))

        if len(elem.children):
            if isinstance(elem.children[0], str):
                defer.returnValue((elem.name, b64decode(elem.children[0])))
            else:
                defer.returnValue((elem.name, elem.children[0]))
        else:
            defer.returnValue((elem.name, b64decode('')))





class ClientFactory(protocol.ClientFactory):
    protocol = ClientProtocol
    resource = 'Twisted'
    ssl_ctx = ssl.ClientContextFactory()


    def __init__(self, credential, domain):
        self.credential = credential
        self.domain = domain


    def clientConnectionLost(self, connector, reason):
        print 'connection lost', reason



