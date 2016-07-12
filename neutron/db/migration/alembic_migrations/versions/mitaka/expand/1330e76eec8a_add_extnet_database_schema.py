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
    op.create_table('extsegments',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=36), nullable=True),
    sa.Column('types_supported', sa.String(length=36), nullable=True),
    sa.Column('vlan_ids_available', sa.String(length=36), nullable=True),
    sa.Column('tun_ids_available', sa.String(length=36), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('extinterfaces',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=36), nullable=True),
    sa.Column('type', sa.String(length=36), nullable=True),
    sa.Column('node_name', sa.String(length=36), nullable=True),
    sa.Column('ip_address', sa.String(length=36), nullable=True),
    sa.Column('node_driver', sa.String(length=36), nullable=True),
    sa.Column('extsegment_id', sa.String(length=36), nullable=True),
    sa.ForeignKeyConstraint(['extsegment_id'], ['extsegments.id']),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('extports',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=36), nullable=True),
    sa.Column('segmentation_id', sa.String(length=36), nullable=False),
    sa.Column('extinterface_id', sa.String(length=36), nullable=True),
    sa.ForeignKeyConstraint(['extinterface_id'], ['extinterfaces.id']),
    sa.ForeignKeyConstraint(['id'], ['ports.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    op.create_table('extlinks',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=36), nullable=True),
    sa.Column('type', sa.String(length=36), nullable=True),
    sa.Column('segmentation_id', sa.String(length=36), nullable=True),
    sa.Column('extinterface1_id', sa.String(length=36), nullable=True),
    sa.Column('extinterface2_id', sa.String(length=36), nullable=True),
    sa.Column('network_id', sa.String(length=36), nullable=True),
    sa.ForeignKeyConstraint(['network_id'], ['networks.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['extinterface1_id'], ['extinterfaces.id']),
    sa.ForeignKeyConstraint(['extinterface2_id'], ['extinterfaces.id']),
    sa.PrimaryKeyConstraint('id'),
    mysql_engine='InnoDB'
    )
    ### end Alembic commands ###
