"""Initialize

Revision ID: 8fdef4b583c0
Revises: 
Create Date: 2021-11-27 22:10:23.343681

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8fdef4b583c0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Call SQL to `CREATE EXTENSION IF NOT EXISTS "uuid-ossp"`;
    op.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))


def downgrade():
    op.execute(sa.text('DROP EXTENSION IF EXISTS "uuid-ossp"'))