from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path
from sdrtrunk.consumers import SDRTrunkConsumer

application = ProtocolTypeRouter({
    'websocket': URLRouter([
        path('ws/sdrtrunk/', SDRTrunkConsumer.as_asgi()),
    ]),
})
