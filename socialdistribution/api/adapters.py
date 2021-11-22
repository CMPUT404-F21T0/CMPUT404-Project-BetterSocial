from typing import Dict


class BaseAdapter:
    """Default handlers for a given node connection. Methods should be overridden for each team, as needed."""
    pass


class Team1Adapter(BaseAdapter):
    pass


# A global list of adapters that are tied to nodes via the database.
registered_adapters: Dict[str, BaseAdapter] = {
    'default': BaseAdapter(),
    'team_1': Team1Adapter()
}
