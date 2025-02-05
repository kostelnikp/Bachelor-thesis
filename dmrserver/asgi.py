"""
ASGI config for dmrserver project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from sdrtrunk.consumers import SDRTrunkConsumer
from django.urls import path  # Import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dmrserver.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": URLRouter([
        path('ws/sdrtrunk/', SDRTrunkConsumer.as_asgi()),
    ]),
})

