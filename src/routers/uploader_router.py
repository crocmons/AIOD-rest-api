import abc

from fastapi import APIRouter


class UploaderRouter(abc.ABC):
    @abc.abstractmethod
    def create(self, url_prefix: str) -> APIRouter: ...
