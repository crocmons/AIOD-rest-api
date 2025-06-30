from database.model.bookmark.bookmark import Bookmark
from routers.resource_router import ResourceRouter


class BookmarkRouter(ResourceRouter):
    @property
    def version(self) -> int:
        return 1

    @property
    def resource_name(self) -> str:
        return "bookmark"

    @property
    def resource_name_plural(self) -> str:
        return "bookmarks"

    @property
    def resource_class(self) -> type[Bookmark]:
        return Bookmark
