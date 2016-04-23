from alembic import op
import sqlalchemy as sa


def upgrade():
    op.create_table(
        'extsegment',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=36), nullable=True),
        sa.Column('network_id', sa.String(length=36), nullable=False),
        sa.Column('extsegment_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['network_id'], ['networks.id'],
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['extsegment_id'], ['extsegments.id'],
                                ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
