import contextlib
from typing import cast
from unittest.mock import Mock

from authentication import KeycloakUser, keycloak_openid, REVIEWER_ROLE
from database.authorization import register_user, set_permission, PermissionType
from database.model.concept.aiod_entry import EntryStatus
from database.model.concept.concept import AIoDConcept
from database.review import Submission, Review, Decision
from database.session import DbSession

ALICE = KeycloakUser("Alice", set(), "alice-sub")
BOB = KeycloakUser("Bob", set(), "bob-sub")
REVIEWER = KeycloakUser("Reviewer", {cast(str, REVIEWER_ROLE)}, "reviewer-sub")


def _register_user_in_db(user: KeycloakUser) -> KeycloakUser:
    with DbSession() as session:
        register_user(user, session)
        session.commit()
    return user


def kc_user_with_roles(*roles: str) -> KeycloakUser:
    """ Generates a user with name 'Dummy' and identifier 'Foo' and the provided roles. """
    return KeycloakUser(
        name="Dummy",
        roles=set(roles),
        _subject_identifier="Foo",
    )

@contextlib.contextmanager
def logged_in_user(user: KeycloakUser | None):
    original = keycloak_openid.introspect
    keycloak_openid.introspect = Mock(
        return_value={
            "realm_access": {"roles": user.roles},
            "resource_access": {
                "account": {"roles": ["manage-account", "manage-account-links", "view-profile"]}
            },
            "scope": "openid profile email",
            "username": user.name,
            "token_type": "Bearer",
            "active": True,
            "sub": user._subject_identifier,
        }
    ) if user else None
    yield
    keycloak_openid.introspect = original


def register_asset(asset: AIoDConcept, /, *, owner: KeycloakUser, status: EntryStatus):
    with DbSession() as session:
        session.add(asset)
        session.commit()

        register_user(owner, session)
        set_permission(owner, asset.aiod_entry, session, type_=PermissionType.ADMIN)

        asset.aiod_entry.status = status
        if status in [EntryStatus.SUBMITTED, EntryStatus.PUBLISHED, EntryStatus.REJECTED]:
            submission = Submission(
                requestee_identifier=owner._subject_identifier,
                aiod_entry_identifier=asset.aiod_entry.identifier,
                asset_type=asset.__tablename__,
            )
            session.add(submission)
            if status == EntryStatus.PUBLISHED:
                register_user(REVIEWER, session)
                review = Review(
                    decision=Decision.ACCEPTED,
                    reviewer_identifier=REVIEWER._subject_identifier,
                    comment="foo",
                )
                review.submission = submission
                session.add(review)
        session.commit()
        return asset.identifier
