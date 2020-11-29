import logging
from .trace import format_query


class QueryLogHandler(logging.StreamHandler):

    def emit(self, record):
        try:
            #msg = self.format(record)
            msg = format_query(record.getMessage())

            stream = self.stream
            # issue 35046: merged two stream.writes into one.
            stream.write(msg + self.terminator)
            self.flush()
        except RecursionError:  # See issue 36272
            raise
        except Exception:
            self.handleError(record)
