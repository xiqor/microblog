"""new fields in user model

Revision ID: 84471579b908
Revises: 9eddb280b073
Create Date: 2025-02-07 14:23:33.176551

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '84471579b908'
down_revision = '9eddb280b073'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('about_me', sa.String(length=140), nullable=True))
        batch_op.add_column(sa.Column('last_seen', sa.DateTime(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('last_seen')
        batch_op.drop_column('about_me')

    # ### end Alembic commands ###
