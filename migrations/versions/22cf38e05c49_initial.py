"""initial

Revision ID: 22cf38e05c49
Revises: 
Create Date: 2022-10-03 15:33:14.421496

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '22cf38e05c49'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('storm',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('operational_id', sa.String(length=255), nullable=True),
    sa.Column('start_date', sa.DateTime(), nullable=False),
    sa.Column('end_date', sa.DateTime(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('year', sa.Integer(), nullable=False),
    sa.Column('season', sa.Integer(), nullable=False),
    sa.Column('basin', sa.String(length=255), nullable=False),
    sa.Column('source_info', sa.String(length=255), nullable=True),
    sa.Column('source_method', sa.String(length=255), nullable=True),
    sa.Column('source_url', sa.String(length=255), nullable=True),
    sa.Column('source', sa.String(length=255), nullable=True),
    sa.Column('ace', sa.Float(), nullable=True),
    sa.Column('prob_2day', sa.String(length=255), nullable=True),
    sa.Column('prob_5day', sa.String(length=255), nullable=True),
    sa.Column('risk_2day', sa.String(length=255), nullable=True),
    sa.Column('risk_5day', sa.String(length=255), nullable=True),
    sa.Column('realtime', sa.Boolean(), nullable=False),
    sa.Column('invest', sa.Boolean(), nullable=False),
    sa.Column('update_time', sa.DateTime(), nullable=False),
    sa.Column('date', sa.PickleType(), nullable=False),
    sa.Column('type', sa.PickleType(), nullable=False),
    sa.Column('lat', sa.PickleType(), nullable=False),
    sa.Column('lon', sa.PickleType(), nullable=False),
    sa.Column('vmax', sa.PickleType(), nullable=False),
    sa.Column('mslp', sa.PickleType(), nullable=False),
    sa.Column('extra_obs', sa.PickleType(), nullable=True),
    sa.Column('special', sa.PickleType(), nullable=True),
    sa.Column('wmo_basin', sa.PickleType(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('storm_forecast',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('storm_id', sa.String(), nullable=True),
    sa.Column('init', sa.DateTime(), nullable=False),
    sa.Column('fhr', sa.PickleType(), nullable=False),
    sa.Column('lat', sa.PickleType(), nullable=False),
    sa.Column('lon', sa.PickleType(), nullable=False),
    sa.Column('vmax', sa.PickleType(), nullable=False),
    sa.Column('mslp', sa.PickleType(), nullable=False),
    sa.Column('type', sa.PickleType(), nullable=False),
    sa.Column('windrad', sa.PickleType(), nullable=False),
    sa.Column('cumulative_ace', sa.PickleType(), nullable=False),
    sa.Column('cumulative_ace_fhr', sa.PickleType(), nullable=False),
    sa.ForeignKeyConstraint(['storm_id'], ['storm.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('storm_forecast')
    op.drop_table('storm')
    # ### end Alembic commands ###
