"""Added all tables

Revision ID: 3f447094a063
Revises: 8b78d4dc9d2c
Create Date: 2025-08-19 23:02:35.560769

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3f447094a063'
down_revision: Union[str, Sequence[str], None] = '8b78d4dc9d2c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
