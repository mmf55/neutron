# Copyright 2016 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

"""Add extnet database schema

Revision ID: 1330e76eec8a
Revises: 0e66c5227a8a
Create Date: 2016-05-02 15:09:03.694752

"""

# revision identifiers, used by Alembic.
revision = '1330e76eec8a'
down_revision = '0e66c5227a8a'

from alembic import op
import sqlalchemy as sa



def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('extnodeints',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=36), nullable=True),
    sa.Column('type', sa.String(length=36), nullable=True),
    sa.Column('extnodename', sa.String(length=36), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('extconnections',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('types_supported', sa.String(length=36), nullable=True),
    sa.Column('ids_pool', sa.String(length=36), nullable=True),
    sa.Column('extnodeint1_id', sa.String(length=36), nullable=True),
    sa.Column('extnodeint2_id', sa.String(length=36), nullable=True),
    sa.ForeignKeyConstraint(['extnodeint1_id'], ['extnodeints.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['extnodeint2_id'], ['extnodeints.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('extports',
    sa.Column('port_id', sa.String(length=36), nullable=False),
    sa.Column('access_id', sa.String(length=36), nullable=True),
    sa.Column('extnodeint_id', sa.String(length=36), nullable=True),
    sa.ForeignKeyConstraint(['extnodeint_id'], ['extnodeints.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['port_id'], ['ports.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('port_id'),
    mysql_engine='InnoDB'
    )
    op.create_table('extlinks',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('type', sa.String(length=36), nullable=True),
    sa.Column('overlay_id', sa.String(length=36), nullable=True),
    sa.Column('extport_id', sa.String(length=36), nullable=True),
    sa.Column('extconnection_id', sa.String(length=36), nullable=True),
    sa.ForeignKeyConstraint(['extconnection_id'], ['extconnections.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['extport_id'], ['extports.port_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    ### end Alembic commands ###
