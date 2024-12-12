import pytest

from database.model.concept.aiod_entry import EntryStatus


def test_user_must_be_logged_in_to_publish():
    # with pytest.raises(Exception):
    #     ...  # Try upload without authentication
    ...


def test_new_asset_is_draft():
    # Authenticated Upload
    # Fetch status from server
    # assert is draft
    ...


def test_drafts_are_private():
    ...
    # Try access asset directly
    # through list
    # through ES
    # with and without authentication


def test_user_can_submit_draft_for_review():
    ...  # Test submit transitions from "draft" to "submitted"


def test_user_can_revoke_submission():
    ...  # Test revoke transitions from "submitted" status to "draft"


@pytest.mark.parametrize("status", EntryStatus)
def test_user_can_always_delete_asset(status: EntryStatus):
    assert ..., f"User should be able to delete their asset in '{status}' status"


def test_user_can_edit_asset_in_draft():
    assert ..., "Users should be able to edit their asset while in draft."


def test_user_cannot_edit_asset_in_submission():
    assert ..., "Users can not edit assets under submission."
    # This is the avoid race conditions with the reviewer workflow


def test_only_reviewer_can_approve_submission():
    assert ..., "Only reviewers should be able to approve a submission"
    assert ..., "Reviewers should be able to approve submissions"
    assert ..., "An accepted submission should result in 'published' status."


def test_reviewer_cannot_approve_own_submission():
    assert ..., "A user cannot approve their own submission."
