from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.settings  import api_settings as settings
from rest_framework.response import Response

class ResultSetPagination(PageNumberPagination):
    page_size=getattr(settings,'PAGE_SIZE',10)
    max_page_size=getattr(settings,'MAX_PAGE_SIZE',100)
    page_size_query_param=getattr(settings,'PAGE_SIZE_QUERY_PARAM','limit')

    def get_paginated_response(self, data):
        response=PageNumberPagination.get_paginated_response(self,data)
        response.data['code']=0
        response.data['msg']=""
        return response