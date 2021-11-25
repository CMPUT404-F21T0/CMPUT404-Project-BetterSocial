from typing import Dict

from rest_framework.request import Request


class BaseAdapter:
    """Default handlers for a given node connection. Methods should be overridden for each team, as needed."""

    def postInboxItem(self, request: Request, *args, **kwargs) -> Request:
        return request


class Team1Adapter(BaseAdapter):
    pass


class Team4Adapter(BaseAdapter):
    pass


# A global list of adapters that are tied to nodes via the database.
registered_adapters: Dict[str, BaseAdapter] = {
    'default': BaseAdapter(),
    'team_1': Team1Adapter(),
    'team_4': Team1Adapter(),
}
