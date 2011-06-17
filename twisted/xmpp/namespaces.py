from twisted.words.protocols.jabber.xmlstream import NS_STREAMS, NS_XMPP_TLS
from twisted.words.protocols.jabber.sasl import NS_XMPP_SASL
from twisted.words.protocols.jabber.client import NS_XMPP_BIND, NS_XMPP_SESSION, NS_XMPP_STREAMS

NS_JABBER_SERVER = 'jabber:server'
NS_JABBER_CLIENT = 'jabber:client'

NS_CAPS = 'http://jabber.org/protocol/caps'


__all__ = (
    'NS_CAPS',
    'NS_JABBER_SERVER', 'NS_JABBER_CLIENT',
    'NS_STREAMS', 
    'NS_XMPP_TLS', 'NS_XMPP_STREAMS', 'NS_XMPP_SASL', 'NS_XMPP_BIND', 'NS_XMPP_SESSION'
)



