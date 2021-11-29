from uuid import UUID


class BetterUUIDConverter:
    """UUID matcher that accepts any amount of dashes"""

    regex = r'(?:[0-9a-fA-F]-*){32}'

    def to_python(self, value: str):
        return UUID(value)

    def to_url(self, value: UUID):
        return str(value)
