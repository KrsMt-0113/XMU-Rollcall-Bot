"""API namespace base class."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import TronClassClient


class APINamespace:
    def __init__(self, client: "TronClassClient"):
        self._client = client

    def _get(self, path, **kw):
        return self._client._get(path, **kw)

    def _post(self, path, **kw):
        return self._client._post(path, **kw)

    def _put(self, path, **kw):
        return self._client._put(path, **kw)

    def _delete(self, path, **kw):
        return self._client._delete(path, **kw)
