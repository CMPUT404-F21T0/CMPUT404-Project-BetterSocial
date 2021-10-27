from django.core.exceptions import ValidationError
from rest_framework import serializers


def validate_categories(value):
    """Ensure that the value is a JSON list of non-empty strings, and nothing else"""

    # Reuse the rest_framework validators, asking that every child must be a CharField
    serializer = serializers.ListSerializer(data = value, child = serializers.CharField(min_length = 1))

    # Encasing serializer.errors in a list ensures that it does not come to some weird error where ValidationError expects a list and gets a dict instead. It happened when there was vlid JSOn but it wasn't a list (ex. pass a string or a dict)
    if not serializer.is_valid():
        raise ValidationError(["Categories should be a list of non-empty strings.", serializer.errors])
