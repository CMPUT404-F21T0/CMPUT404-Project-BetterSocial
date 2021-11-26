from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnList


class CustomPageNumberPagination(PageNumberPagination):
    page_size = 5
    page_query_param = 'page'
    page_size_query_param = 'size'

    def get_paginated_response(self, data: ReturnList):
        """don't modify the response structure because the api does not call for it"""
        return Response(data)
