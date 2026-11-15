from rest_framework.exceptions import APIException, NotAuthenticated


class Unauthorized(APIException):
    status_code = NotAuthenticated.status_code
    default_detail = NotAuthenticated.default_detail
    default_code = NotAuthenticated.default_code
