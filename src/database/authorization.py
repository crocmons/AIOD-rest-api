import enum

import sqlalchemy
from sqlalchemy import Column
from sqlmodel import SQLModel, Field, Relationship

from authentication import User
from database.model.concept.aiod_entry import AIoDEntryORM


class RegisteredUser(SQLModel, table=True):  # type: ignore [call-arg]
    """A user which is explicitly registered or uploaded an asset."""

    __tablename__ = "user"
    subject_identifier: str = Field(primary_key=True)


class PermissionType(enum.StrEnum):
    READ = enum.auto()
    WRITE = enum.auto()
    ADMIN = enum.auto()


class Permission(SQLModel, table=True):  # type: ignore [call-arg]
    # - [ ] Add group reference:
    #   - [ ] expand primary key to triplet
    #   - [ ] either group or user needs to be None
    aiod_entry_identifier: int = Field(foreign_key="aiod_entry.identifier", primary_key=True)
    aiod_entry: AIoDEntryORM = Relationship(
        back_populates="permissions",
    )
    user_identifier: str = Field(foreign_key="user.subject_identifier", primary_key=True)

    type_: PermissionType = Field(
        sa_column=Column(sqlalchemy.Enum(PermissionType)), default=PermissionType.READ
    )


def user_can_read(user: User, aiod_entry) -> bool:
    # TODO:
    #  - [ ] add option for private entries
    #  - [ ] check if any permissions exist (read is least permissive)
    return True


def user_can_write(user: User, aiod_entry) -> bool:
    # TODO: check for write or admin permission
    return False


def user_can_administer(user: User, aiod_entry) -> bool:
    # TODO: check for write or admin permission
    return False
