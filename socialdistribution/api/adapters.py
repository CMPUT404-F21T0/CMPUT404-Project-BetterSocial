from typing import Dict, Union
from uuid import UUID

import requests
from requests.auth import HTTPBasicAuth
from rest_framework.request import Request
from yarl import URL


class BaseAdapter:
    """Default handlers for a given node connection. Methods should be overridden for each team, as needed."""

    def __init__(self) -> None:
        super().__init__()

        self.session = requests.session()
        self.session.headers['Accept'] = 'application/json'

    def post_inbox_item(self, request: Request, *args, **kwargs) -> Request:
        return request

    def get_author(self, node, author_uuid: Union[str, UUID], *args, **kwargs) -> requests.Response:
        return self.session.get(
            self.get_author_url(node, author_uuid),
            auth = HTTPBasicAuth(node.node_username, node.node_password)
        )

    def get_authors(self, node, *args, **kwargs) -> requests.Response:
        return self.session.get(
            self.get_authors_url(node),
            params = { 'size': 1000 },
            headers = { 'Accept': 'application/json' },
            auth = HTTPBasicAuth(node.node_username, node.node_password)
        )

    def get_author_url(self, node, author_uuid: Union[str, UUID], *args, **kwargs) -> str:
        if isinstance(author_uuid, UUID):
            author_uuid = str(author_uuid)

        return (URL(node.host) / node.prefix / 'author' / author_uuid / '').human_repr()

    def get_authors_url(self, node, *args, **kwargs) -> str:
        return (URL(node.host) / node.prefix / 'authors' / '').human_repr()

    def get_followers(self, node, author_uuid: Union[str, UUID], *args, **kwargs):
        if isinstance(author_uuid, UUID):
            author_uuid = str(author_uuid)

        return self.session.get(
            self.get_followers_url(node, author_uuid),
            auth = HTTPBasicAuth(node.node_username, node.node_password)
        )

    def get_followers_url(self, node, author_uuid: Union[str, UUID], *args, **kwargs) -> str:
        if isinstance(author_uuid, UUID):
            author_uuid = str(author_uuid)

        return (URL(node.host) / node.prefix / 'author' / author_uuid / 'followers' / '').human_repr()


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
