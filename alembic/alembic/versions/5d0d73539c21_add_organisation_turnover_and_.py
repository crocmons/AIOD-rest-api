"""Add organisation.turnover and organisation.number_of_employees

Revision ID: 5d0d73539c21
Revises: 1662d64ebe23
Create Date: 2025-05-12 14:00:35.644646

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d0d73539c21'
down_revision: Union[str, None] = '1662d64ebe23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
