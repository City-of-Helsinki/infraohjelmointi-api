import json
import logging
import time
import uuid

logger = logging.getLogger("infraohjelmointi_api")

def generate_streaming_response(queryset, serializer_class, endpoint, chunk_size=1000):
    """
    Generates a streaming response for a given queryset using the provided serializer with chunking.

    Args:
        queryset: The Django queryset to serialize.
        serializer_class: The Django REST Framework serializer class to use.
        chunk_size: The number of serialized items to include in each chunk.

    Yields:
        str: A chunk of the JSON response.
    """
    serializer = serializer_class(many=False)

    def data_generator():
        logger.info(
            "Started to generate endpoint {} data".format(endpoint)
        )
        start = time.time()
        yield '['
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
                yield (',' if not first else '') + ','.join(item_buffer)
                item_buffer = []
                first = False

        if item_buffer:
            yield (',' if not first else '') + ','.join(item_buffer)

        yield ']'
        end = time.time()
        logger.info(
            "Finished generating endpoint {} data in {} seconds".format(endpoint, round(end-start, 3))
        )
    return data_generator()