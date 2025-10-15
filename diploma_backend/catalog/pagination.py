from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class FrontPagePagination(PageNumberPagination):
    page_query_param = "currentPage"
    page_size_query_param = "limit"
    page_size = 20

    def get_pagination_response(self, data):
        return Response({
            "items": data,
            "currentPage": self.page.number,
            "lastPage": self.page.paginator.num_pages,
        })
