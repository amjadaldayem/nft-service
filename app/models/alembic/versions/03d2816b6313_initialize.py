"""Initialize

Revision ID: 03d2816b6313
Revises: 
Create Date: 2021-12-12 16:20:32.061126

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '03d2816b6313'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))


def downgrade():
    op.execute(sa.text('DROP EXTENSION IF EXISTS "uuid-ossp"'))
