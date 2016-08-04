"""Keep track of phrase frequency

Revision ID: cb4ccccf9de2
Revises:
Create Date: 2016-08-01 00:01:03.944195

"""

# revision identifiers, used by Alembic.
revision = 'cb4ccccf9de2'
down_revision = None
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


table = 'phrase'


def upgrade():
    op.add_column(table,
                  sa.Column('first_observed_at', sa.DateTime(timezone=False)))
    op.alter_column(table, 'observed_at', new_column_name='last_observed_at')


def downgrade():
    op.drop_column(table, 'first_observed_at')
    op.alter_column(table, 'last_observed_at', new_column_name='observed_at')
