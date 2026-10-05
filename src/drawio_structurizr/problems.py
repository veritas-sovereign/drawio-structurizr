"""Problems found while reading and converting diagrams."""


class Problem:
    """A finding with a stable code; severity is "error" or "warning".

    Errors mean Structurizr would reject the output, so nothing is written.
    Warnings only stop the output with --strict.
    """

    def __init__(self, code, severity, message):
        self.code = code
        self.severity = severity
        self.message = message

    def __str__(self):
        return f'[{self.code}] {self.severity}: {self.message}'

    def __repr__(self):
        return f'Problem({self.code!r}, {self.severity!r}, {self.message!r})'

    def as_dict(self):
        return {'code': self.code, 'severity': self.severity, 'message': self.message}

    def __eq__(self, other):
        return isinstance(other, Problem) and self.as_dict() == other.as_dict()
