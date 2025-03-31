import json
import logging
import time
import uuid

from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger("infraohjelmointi_api")


def generate_streaming_response(
    queryset, serializer_class, user_id, endpoint, chunk_size=1000
):
    """
    Generates a streaming response for a given queryset using the provided serializer with chunking.

    Args:
        queryset: The Django queryset to serialize.
        serializer_class: The Django REST Framework serializer class to use.
        user_id: The id for the request user.
        endpoint: The name for the endpoint that will be used on logging.
        chunk_size: The number of serialized items to include in each chunk.

    Yields:
        str: A chunk of the JSON response.
    """
    serializer = serializer_class(many=False)

    def data_generator():
        start = time.time()
        yield "["
        first = True
        item_buffer = []
        for item in queryset:
            serialized_data = serializer.to_representation(item)

            def convert_uuid_to_str(obj):
                if isinstance(obj, uuid.UUID):
                    return str(obj)
                return obj

            json_string = json.dumps(serialized_data, default=convert_uuid_to_str)
            item_buffer.append(json_string)

            if len(item_buffer) >= chunk_size:
                yield ("," if not first else "") + ",".join(item_buffer)
                item_buffer = []
                first = False

        if item_buffer:
            yield ("," if not first else "") + ",".join(item_buffer)

        yield "]"
        end = time.time()
        logger.info(
            "User {} request to generate endpoint {} data finished in {} seconds".format(
                user_id, endpoint, round(end - start, 3)
            )
        )

    return data_generator()


def generate_response(self, user_id, pk, endpoint):
    """
    Generates a serialized response.

    Args:
        self: The instance of the class.
        user_id: The id for the request user.
        pk: The primary key of the object to retrieve (UUID).
        endpoint: The endpoint name for logging.
    """
    try:
        uuid.UUID(str(pk))
        queryset = self.get_queryset()
        obj = queryset.get(pk=pk)
        serializer = self.get_serializer(obj)
    except ValueError:
        return generate_response_value_error(user_id, endpoint)
    except Exception as e:
        return generate_response_not_found(user_id, endpoint)

    logger.info(
        "User {} request to fetch endpoint {} data finished".format(
            user_id, endpoint
        )
    )
    return Response(serializer.data)

def generate_response_not_found(user_id, endpoint):
    logger.warning(
        "User {} request to fetch endpoint {} data failed".format(
            user_id, endpoint
        )
    )

    return Response(
        data={"error": "Not found"}, status=status.HTTP_404_NOT_FOUND
    )

def generate_response_value_error(user_id, endpoint):
    logger.warning(
        "User {} request to fetch endpoint {} data failed".format(
            user_id, endpoint
        )
    )

    return Response(
        data={"error":"Invalid UUID"}, status=status.HTTP_400_BAD_REQUEST
    )

def send_logger_api_generate_data_start(user_id, endpoint):
    return logger.info(
        "User {} requested to generate endpoint {} data".format(user_id, endpoint)
    )
