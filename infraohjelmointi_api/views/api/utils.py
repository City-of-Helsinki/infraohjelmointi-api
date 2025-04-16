import json
import logging
import time
from typing import AsyncGenerator
import uuid

from rest_framework import status
from rest_framework.response import Response
from asgiref.sync import sync_to_async

logger = logging.getLogger("infraohjelmointi_api")


async def generate_streaming_response(
    queryset, serializer_class, user_id, endpoint, chunk_size=1000, serializer_context={}
) -> AsyncGenerator[str, None]:
    """
    Generates a streaming response for a given queryset using the provided serializer with chunking.

    Args:
        queryset: The Django queryset to serialize.
        serializer_class: The Django REST Framework serializer class to use.
        user_id: The id for the request user.
        endpoint: The name for the endpoint that will be used on logging.
        chunk_size: The number of serialized items to include in each chunk.
        serializer_context: Context that will be passed to the serializer.

    Yields:
        str: A chunk of the JSON response.
    """
    serializer = serializer_class(many=False, context=serializer_context)
    async_to_representation = sync_to_async(serializer.to_representation, thread_sensitive=True)

    start = time.time()
    yield "["
    first = True
    item_buffer = []
    item_index = 0

    try:
        async for item in queryset:
            item_index += 1

            try:
                serialized_data = await async_to_representation(item)

                json_string = json.dumps(serialized_data, default=str)
                item_buffer.append(json_string)

                if len(item_buffer) >= chunk_size:
                    yield ("," if not first else "") + ",".join(item_buffer)
                    item_buffer = []
                    first = False

            except Exception as item_error:
                item_id = getattr(item, 'id', 'N/A')
                logger.error(f"Error serializing item {item_index} (ID: {item_id}) in endpoint {endpoint}: {item_error}", exc_info=True)

                raise item_error

        if item_buffer:
            yield ("," if not first else "") + ",".join(item_buffer)

        yield "]"

    except Exception as outer_error:
        logger.error(f"Error during queryset iteration for endpoint {endpoint}: {outer_error}", exc_info=True)

    finally:
        end = time.time()
        logger.info(
            "User {} request to generate endpoint {} data finished in {} seconds".format(
                user_id, endpoint, round(end - start, 3)
            )
        )


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
    except Exception:
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
