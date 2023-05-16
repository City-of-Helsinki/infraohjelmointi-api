from django_eventstream.consumers import EventsConsumer, Listener
from django_grip import GripMiddleware
from django_eventstream.eventrequest import EventRequest
from django_eventstream.eventstream import EventPermissionError
from django_eventstream.utils import sse_error_response, add_default_headers
from overrides import override
from django.http import HttpResponseBadRequest
import asyncio
import six
from channels.http import AsgiRequest

import environ

env = environ.Env()

import logging

logger = logging.getLogger("infraohjelmointi_api")


class CostomEventConsumer(EventsConsumer):
    @override
    async def handle(self, body):
        """Original method does not support multi host for CORS"""
        self.listener = None

        request = AsgiRequest(self.scope, body)

        def dummy_get_response(request):
            return None

        gm = GripMiddleware(dummy_get_response)
        gm.process_request(request)

        if "user" in self.scope:
            request.user = self.scope["user"]

        if "session" in self.scope:
            request.session = self.scope["session"]

        try:
            event_request = await self.parse_request(request)
            response = None
        except EventRequest.ResumeNotAllowedError as e:
            response = HttpResponseBadRequest("Invalid request: %s.\n" % str(e))
        except EventRequest.GripError as e:
            if request.grip.proxied:
                response = sse_error_response(
                    "internal-error", "Invalid internal request."
                )
            else:
                response = sse_error_response(
                    "bad-request", "Invalid request: %s." % str(e)
                )
        except EventRequest.Error as e:
            response = sse_error_response(
                "bad-request", "Invalid request: %s." % str(e)
            )

        # for grip requests, prepare immediate response
        if not response and request.grip.proxied:
            try:
                event_response = await self.get_events(event_request)
                response = event_response.to_http_response(request)
            except EventPermissionError as e:
                response = sse_error_response(
                    "forbidden", str(e), {"channels": e.channels}
                )

        extra_headers = {}

        add_default_headers(extra_headers)

        # workaround to support multi CORS origin
        CORS_ALLOWED_ORIGINS = env("ALLOWED_CORS_ORIGINS")
        if request.META["HTTP_ORIGIN"] in CORS_ALLOWED_ORIGINS:
            extra_headers["Access-Control-Allow-Origin"] = request.META["HTTP_ORIGIN"]

        # if this was a grip request or we encountered an error, respond now
        if response:
            response = gm.process_response(request, response)

            headers = []
            for name, value in response.items():
                if isinstance(name, six.text_type):
                    name = name.encode("utf-8")
                if isinstance(value, six.text_type):
                    value = value.encode("utf-8")
                headers.append((name, value))

            for name, value in extra_headers.items():
                if isinstance(name, six.text_type):
                    name = name.encode("utf-8")
                if isinstance(value, six.text_type):
                    value = value.encode("utf-8")
                headers.append((name, value))

            await self.send_response(
                response.status_code, response.content, headers=headers
            )
            return

        # if we got here then the request was not a grip request, and there
        #   were no errors, so we can begin a local stream response

        headers = [(six.b("Content-Type"), six.b("text/event-stream"))]
        for name, value in extra_headers.items():
            if isinstance(name, six.text_type):
                name = name.encode("utf-8")
            if isinstance(value, six.text_type):
                value = value.encode("utf-8")
            headers.append((name, value))

        await self.send_headers(headers=headers)

        self.listener = Listener()
        self.is_streaming = True

        asyncio.get_event_loop().create_task(self.stream(event_request))
