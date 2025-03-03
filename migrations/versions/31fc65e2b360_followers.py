"""followers

Revision ID: 31fc65e2b360
Revises: 84471579b908
Create Date: 2025-02-21 15:33:15.769085

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '31fc65e2b360'
down_revision = '84471579b908'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('followers',
    sa.Column('follower_id', sa.Integer(), nullable=False),
    sa.Column('followed_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['followed_id'], ['user.id'], ),
    sa.ForeignKeyConstraint(['follower_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('follower_id', 'followed_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('followers')
    # ### end Alembic commands ###
