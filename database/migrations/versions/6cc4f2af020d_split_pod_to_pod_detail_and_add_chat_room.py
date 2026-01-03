"""split_pod_to_pod_detail_and_add_chat_room

Revision ID: 6cc4f2af020d
Revises: 5bb3f1af019c
Create Date: 2025-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '6cc4f2af020d'
down_revision = '5bb3f1af019c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    1. Pod 모델 분리: PodDetail 테이블 생성
    2. Pod 모델에서 PodDetail로 이동할 필드 제거
    3. ChatRoom, ChatMember 테이블 생성
    4. Pod에 chat_room_id 추가
    5. ChatMessage에 chat_room_id 추가
    6. is_active를 is_del로 변경
    """
    
    # 테이블 존재 여부 확인을 위한 connection 가져오기
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    
    # 1. PodDetail 테이블 생성 (존재하지 않을 때만)
    if 'pod_details' not in existing_tables:
        op.create_table(
            'pod_details',
            sa.Column('pod_id', sa.Integer(), nullable=False),
            sa.Column('description', sa.String(length=500), nullable=True),
            sa.Column('image_url', sa.String(length=500), nullable=True),
            sa.Column('address', sa.String(length=300), nullable=False),
            sa.Column('sub_address', sa.String(length=300), nullable=True),
            sa.Column('x', sa.Float(), nullable=True, comment='경도 (longitude)'),
            sa.Column('y', sa.Float(), nullable=True, comment='위도 (latitude)'),
            sa.Column('chat_channel_url', sa.String(length=255), nullable=True, comment='채팅방 URL (deprecated - Pod.chat_room_id 사용)'),
            sa.ForeignKeyConstraint(['pod_id'], ['pods.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('pod_id')
        )
        
        # 2. PodDetail로 데이터 마이그레이션 (기존 pods 테이블에서)
        # pods 테이블에 해당 컬럼이 있는지 확인 후 마이그레이션
        pod_columns = [col['name'] for col in inspector.get_columns('pods')]
        if 'description' in pod_columns:
            op.execute("""
                INSERT INTO pod_details (pod_id, description, image_url, address, sub_address, x, y, chat_channel_url)
                SELECT id, description, image_url, address, sub_address, x, y, chat_channel_url
                FROM pods
                WHERE id NOT IN (SELECT pod_id FROM pod_details)
            """)
    else:
        # 테이블이 이미 존재하는 경우, 데이터가 없는 경우에만 마이그레이션
        result = bind.execute(sa.text("SELECT COUNT(*) FROM pod_details"))
        if result.scalar() == 0:
            pod_columns = [col['name'] for col in inspector.get_columns('pods')]
            if 'description' in pod_columns:
                op.execute("""
                    INSERT INTO pod_details (pod_id, description, image_url, address, sub_address, x, y, chat_channel_url)
                    SELECT id, description, image_url, address, sub_address, x, y, chat_channel_url
                    FROM pods
                    WHERE id NOT IN (SELECT pod_id FROM pod_details)
                """)
    
    # 3. Pod 테이블에서 PodDetail로 이동한 필드 제거 (존재하는 경우에만)
    pod_columns = [col['name'] for col in inspector.get_columns('pods')]
    if 'description' in pod_columns:
        op.drop_column('pods', 'description')
    if 'image_url' in pod_columns:
        op.drop_column('pods', 'image_url')
    if 'address' in pod_columns:
        op.drop_column('pods', 'address')
    if 'sub_address' in pod_columns:
        op.drop_column('pods', 'sub_address')
    if 'x' in pod_columns:
        op.drop_column('pods', 'x')
    if 'y' in pod_columns:
        op.drop_column('pods', 'y')
    if 'chat_channel_url' in pod_columns:
        op.drop_column('pods', 'chat_channel_url')
    
    # 4. is_active를 is_del로 변경 (기본값 반전: True -> False)
    pod_columns = [col['name'] for col in inspector.get_columns('pods')]
    if 'is_del' not in pod_columns:
        op.add_column('pods', sa.Column('is_del', sa.Boolean(), nullable=False, server_default='0'))
        if 'is_active' in pod_columns:
            op.execute("UPDATE pods SET is_del = NOT is_active WHERE is_active IS NOT NULL")
    if 'is_active' in pod_columns:
        op.drop_column('pods', 'is_active')
    
    # 5. ChatRoom 테이블 생성
    if 'chat_rooms' not in existing_tables:
        op.create_table(
            'chat_rooms',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('pod_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False, comment='채팅방 이름'),
            sa.Column('cover_url', sa.String(length=500), nullable=True, comment='채팅방 커버 이미지 URL'),
            sa.Column('room_metadata', sa.Text(), nullable=True, comment='채팅방 메타데이터 (JSON)'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1', comment='활성화 여부'),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(['pod_id'], ['pods.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('pod_id')
        )
        op.create_index(op.f('ix_chat_rooms_pod_id'), 'chat_rooms', ['pod_id'], unique=False)
    
    # 6. ChatMember 테이블 생성
    if 'chat_members' not in existing_tables:
        op.create_table(
            'chat_members',
            sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
            sa.Column('chat_room_id', sa.Integer(), nullable=False, comment='채팅방 ID'),
            sa.Column('user_id', sa.Integer(), nullable=False, comment='사용자 ID'),
            sa.Column('role', sa.String(length=20), nullable=False, server_default='member', comment='역할 (owner, admin, member)'),
            sa.Column('joined_at', sa.DateTime(), nullable=False, comment='참여 시간'),
            sa.Column('left_at', sa.DateTime(), nullable=True, comment='나간 시간 (null이면 참여 중)'),
            sa.ForeignKeyConstraint(['chat_room_id'], ['chat_rooms.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('chat_room_id', 'user_id', name='uq_chat_members_room_user')
        )
        op.create_index(op.f('ix_chat_members_chat_room_id'), 'chat_members', ['chat_room_id'], unique=False)
        op.create_index(op.f('ix_chat_members_user_id'), 'chat_members', ['user_id'], unique=False)
    
    # 7. Pod에 chat_room_id 추가
    pod_columns = [col['name'] for col in inspector.get_columns('pods')]
    if 'chat_room_id' not in pod_columns:
        op.add_column('pods', sa.Column('chat_room_id', sa.Integer(), nullable=True, comment='채팅방 ID'))
        op.create_foreign_key('fk_pods_chat_room_id', 'pods', 'chat_rooms', ['chat_room_id'], ['id'], ondelete='SET NULL')
        op.create_index(op.f('ix_pods_chat_room_id'), 'pods', ['chat_room_id'], unique=True)
    
    # 8. ChatMessage에 chat_room_id 추가 (기존 channel_url은 유지)
    if 'chat_messages' in existing_tables:
        chat_message_columns = [col['name'] for col in inspector.get_columns('chat_messages')]
        if 'chat_room_id' not in chat_message_columns:
            op.add_column('chat_messages', sa.Column('chat_room_id', sa.Integer(), nullable=True, comment='채팅방 ID'))
            op.create_foreign_key('fk_chat_messages_chat_room_id', 'chat_messages', 'chat_rooms', ['chat_room_id'], ['id'], ondelete='CASCADE')
            op.create_index(op.f('ix_chat_messages_chat_room_id'), 'chat_messages', ['chat_room_id'], unique=False)
    
    # 9. PodImage에 pod_detail_id 컬럼 추가 및 기존 pod_id를 pod_detail_id로 변경
    if 'pod_images' in existing_tables:
        pod_image_columns = [col['name'] for col in inspector.get_columns('pod_images')]
        if 'pod_detail_id' not in pod_image_columns:
            op.add_column('pod_images', sa.Column('pod_detail_id', sa.Integer(), nullable=True, comment='PodDetail ID'))
            if 'pod_id' in pod_image_columns:
                op.execute("UPDATE pod_images pi INNER JOIN pods p ON pi.pod_id = p.id SET pi.pod_detail_id = p.id")
            op.alter_column('pod_images', 'pod_detail_id', 
                            existing_type=sa.Integer(), 
                            nullable=False)
            op.create_foreign_key('fk_pod_images_pod_detail_id', 'pod_images', 'pod_details', ['pod_detail_id'], ['pod_id'], ondelete='CASCADE')
            op.create_index(op.f('ix_pod_images_pod_detail_id'), 'pod_images', ['pod_detail_id'], unique=False)
        # 기존 pod_id 컬럼 제거 (존재하는 경우에만)
        if 'pod_id' in pod_image_columns:
            # 인덱스와 제약조건 제거 시도 (존재하지 않을 수 있음)
            try:
                op.drop_index('ix_pod_images_pod_id', table_name='pod_images')
            except:
                pass
            try:
                op.drop_constraint('pod_images_ibfk_1', 'pod_images', type_='foreignkey')
            except:
                pass
            op.drop_column('pod_images', 'pod_id')
    
    # 10. Application의 ForeignKey는 pod_id를 유지하되, 관계는 pod_detail로 변경 (SQLAlchemy 레벨에서만)
    # 실제 FK는 변경하지 않음 (pod_id는 pods.id를 참조)
    
    # 11. PodReview의 ForeignKey는 pod_id를 유지하되, 관계는 pod_detail로 변경 (SQLAlchemy 레벨에서만)
    # 실제 FK는 변경하지 않음 (pod_id는 pods.id를 참조)


def downgrade() -> None:
    """
    롤백: PodDetail을 Pod로 다시 통합
    """
    
    # 1. PodImage의 pod_detail_id를 pod_id로 되돌리기
    op.add_column('pod_images', sa.Column('pod_id', sa.Integer(), nullable=True))
    op.execute("UPDATE pod_images SET pod_id = pod_detail_id WHERE pod_detail_id IS NOT NULL")
    op.alter_column('pod_images', 'pod_id', 
                    existing_type=sa.Integer(), 
                    nullable=False)
    op.create_foreign_key('pod_images_ibfk_1', 'pod_images', 'pods', ['pod_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_pod_images_pod_id', 'pod_images', ['pod_id'], unique=False)
    op.drop_index(op.f('ix_pod_images_pod_detail_id'), table_name='pod_images')
    op.drop_constraint('fk_pod_images_pod_detail_id', 'pod_images', type_='foreignkey')
    op.drop_column('pod_images', 'pod_detail_id')
    
    # 2. ChatMessage에서 chat_room_id 제거
    op.drop_index(op.f('ix_chat_messages_chat_room_id'), table_name='chat_messages')
    op.drop_constraint('fk_chat_messages_chat_room_id', 'chat_messages', type_='foreignkey')
    op.drop_column('chat_messages', 'chat_room_id')
    
    # 3. Pod에서 chat_room_id 제거
    op.drop_index(op.f('ix_pods_chat_room_id'), table_name='pods')
    op.drop_constraint('fk_pods_chat_room_id', 'pods', type_='foreignkey')
    op.drop_column('pods', 'chat_room_id')
    
    # 4. ChatMember 테이블 삭제
    op.drop_index(op.f('ix_chat_members_user_id'), table_name='chat_members')
    op.drop_index(op.f('ix_chat_members_chat_room_id'), table_name='chat_members')
    op.drop_table('chat_members')
    
    # 5. ChatRoom 테이블 삭제
    op.drop_index(op.f('ix_chat_rooms_pod_id'), table_name='chat_rooms')
    op.drop_table('chat_rooms')
    
    # 6. Pod에 is_active 복원 (is_del에서 변환)
    op.add_column('pods', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
    op.execute("UPDATE pods SET is_active = NOT is_del WHERE is_del IS NOT NULL")
    op.drop_column('pods', 'is_del')
    
    # 7. PodDetail의 데이터를 Pod로 다시 이동
    op.add_column('pods', sa.Column('description', sa.String(length=500), nullable=True))
    op.add_column('pods', sa.Column('image_url', sa.String(length=500), nullable=True))
    op.add_column('pods', sa.Column('address', sa.String(length=300), nullable=True))
    op.add_column('pods', sa.Column('sub_address', sa.String(length=300), nullable=True))
    op.add_column('pods', sa.Column('x', sa.Float(), nullable=True))
    op.add_column('pods', sa.Column('y', sa.Float(), nullable=True))
    op.add_column('pods', sa.Column('chat_channel_url', sa.String(length=255), nullable=True))
    
    op.execute("""
        UPDATE pods p
        INNER JOIN pod_details pd ON p.id = pd.pod_id
        SET p.description = pd.description,
            p.image_url = pd.image_url,
            p.address = pd.address,
            p.sub_address = pd.sub_address,
            p.x = pd.x,
            p.y = pd.y,
            p.chat_channel_url = pd.chat_channel_url
    """)
    
    # 8. PodDetail 테이블 삭제
    op.drop_table('pod_details')
