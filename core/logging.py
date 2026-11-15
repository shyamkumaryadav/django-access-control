import logging
from urllib.parse import urlsplit


class RequestLogFilter(logging.Filter):
    EXCLUDED_PATHS = {"/favicon.ico"}
    EXCLUDED_PREFIXES = ("/static/", "/media/")

    def filter(self, record):
        message = record.getMessage()

        try:
            request_line = message.split('"')[1]
            method, path, _ = request_line.split(" ", 2)
        except (IndexError, ValueError):
            return True

        clean_path = urlsplit(path).path

        if clean_path in self.EXCLUDED_PATHS or clean_path.startswith(
            self.EXCLUDED_PREFIXES
        ):
            return False

        record.msg = f"{method} {path} {record.status_code}"
        record.args = ()

        return True
