from rest_framework import serializers


class UpdateListSerializer(serializers.ListSerializer):
    def update(self, instances, validated_data):
        instance_hash = {index: instance for index, instance in enumerate(instances)}

        result = [
            # calling update of ProjectCreateSerializer
            self.child.update(instance_hash[index], attrs)
            for index, attrs in enumerate(validated_data)
        ]

        return result
