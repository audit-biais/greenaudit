"""Migration multitenant : Partner → User + Organization

Revision ID: 003_multitenant
Revises: 002_monitoring
Create Date: 2026-04-03

Ce que fait cette migration :
1. Crée la table organizations
2. Crée la table users
3. Pour chaque partner existant, crée une organization + un user admin correspondant
4. Ajoute la colonne organization_id sur audits
5. Migre partner_id → organization_id sur chaque audit
6. Supprime l'ancienne colonne partner_id
7. Supprime la table partners
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers
revision = '003_multitenant'
down_revision = '002_monitoring'
branch_labels = None
depends_on = None


def _table_exists(conn, table_name: str) -> bool:
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = :t)"
    ), {"t": table_name})
    return result.scalar()


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
        "WHERE table_name = :t AND column_name = :c)"
    ), {"t": table_name, "c": column_name})
    return result.scalar()


def _index_exists(conn, index_name: str) -> bool:
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = :i)"
    ), {"i": index_name})
    return result.scalar()


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Créer la table organizations (si elle n'existe pas déjà)
    if not _table_exists(conn, 'organizations'):
        op.create_table(
            'organizations',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('contact_email', sa.String(255), nullable=False),
            sa.Column('contact_name', sa.String(255), nullable=True),
            sa.Column('contact_phone', sa.String(50), nullable=True),
            sa.Column('brand_primary_color', sa.String(7), nullable=False, server_default='#1B5E20'),
            sa.Column('brand_secondary_color', sa.String(7), nullable=False, server_default='#2E7D32'),
            sa.Column('logo_data', sa.LargeBinary, nullable=True),
            sa.Column('logo_content_type', sa.String(50), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('stripe_customer_id', sa.String(255), nullable=True),
            sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
            sa.Column('subscription_plan', sa.String(50), nullable=False, server_default='free'),
            sa.Column('subscription_status', sa.String(50), nullable=False, server_default='inactive'),
            sa.Column('audits_this_month', sa.Integer, nullable=False, server_default='0'),
            sa.Column('audits_limit', sa.Integer, nullable=False, server_default='1'),
            sa.Column('audits_reset_month', sa.String(7), nullable=True),
        )

    # 2. Créer la table users (si elle n'existe pas déjà)
    if not _table_exists(conn, 'users'):
        op.create_table(
            'users',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
            sa.Column('email', sa.String(255), unique=True, nullable=False),
            sa.Column('company_name', sa.String(255), nullable=False),
            sa.Column('hashed_password', sa.String(255), nullable=False),
            sa.Column('is_active', sa.Boolean, nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column('organization_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('organizations.id'), nullable=True),
            sa.Column('role', sa.String(50), nullable=False, server_default='member'),
            sa.Column('is_superadmin', sa.Boolean, nullable=False, server_default='false'),
            sa.Column('stripe_customer_id', sa.String(255), nullable=True),
            sa.Column('stripe_subscription_id', sa.String(255), nullable=True),
            sa.Column('subscription_plan', sa.String(50), nullable=False, server_default='free'),
            sa.Column('subscription_status', sa.String(50), nullable=False, server_default='inactive'),
            sa.Column('audits_this_month', sa.Integer, nullable=False, server_default='0'),
            sa.Column('audits_limit', sa.Integer, nullable=False, server_default='1'),
            sa.Column('audits_reset_month', sa.String(7), nullable=True),
        )
    if not _index_exists(conn, 'ix_users_email'):
        op.create_index('ix_users_email', 'users', ['email'])

    # 3. Si partners n'existe pas → DB fraîche, rien à migrer
    if not _table_exists(conn, 'partners'):
        return

    # 4. Ajouter organization_id sur audits EN PREMIER (nullable temporairement)
    if not _column_exists(conn, 'audits', 'organization_id'):
        op.add_column('audits', sa.Column(
            'organization_id',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('organizations.id'),
            nullable=True,
        ))

    # 5. Migrer les partners → organizations + users
    partners = conn.execute(sa.text(
        "SELECT id, email, password_hash, company_name, "
        "brand_primary_color, brand_secondary_color, "
        "contact_name, contact_phone, stripe_customer_id, "
        "is_active FROM partners"
    )).fetchall()

    for p in partners:
        # Vérifier si un user avec cet email existe déjà (signup après refactor)
        existing_user = conn.execute(sa.text(
            "SELECT id, organization_id FROM users WHERE email = :email"
        ), {"email": p.email}).fetchone()

        if existing_user and existing_user.organization_id:
            # User et org déjà créés via signup → juste lier les audits
            org_id = str(existing_user.organization_id)
        else:
            # Créer l'organisation
            org_id = str(uuid.uuid4())
            conn.execute(sa.text("""
                INSERT INTO organizations (id, name, contact_email, contact_name, contact_phone,
                    brand_primary_color, brand_secondary_color, stripe_customer_id,
                    subscription_plan, subscription_status, audits_this_month, audits_limit)
                VALUES (:id, :name, :email, :contact_name, :contact_phone,
                    :primary, :secondary, :stripe_id,
                    'free', 'inactive', 0, 1)
            """), {
                'id': org_id,
                'name': p.company_name,
                'email': p.email,
                'contact_name': p.contact_name,
                'contact_phone': p.contact_phone,
                'primary': p.brand_primary_color or '#1B5E20',
                'secondary': p.brand_secondary_color or '#2E7D32',
                'stripe_id': p.stripe_customer_id,
            })

            if existing_user:
                # User existe mais sans org → lui assigner cette org
                conn.execute(sa.text(
                    "UPDATE users SET organization_id = :org_id, role = 'admin' WHERE id = :uid"
                ), {'org_id': org_id, 'uid': str(existing_user.id)})
            else:
                # Créer le user
                conn.execute(sa.text("""
                    INSERT INTO users (id, email, company_name, hashed_password, is_active,
                        organization_id, role, is_superadmin,
                        subscription_plan, subscription_status, audits_this_month, audits_limit)
                    VALUES (:id, :email, :company_name, :password_hash, :is_active,
                        :org_id, 'admin', false,
                        'free', 'inactive', 0, 1)
                """), {
                    'id': str(p.id),
                    'email': p.email,
                    'company_name': p.company_name,
                    'password_hash': p.password_hash,
                    'is_active': p.is_active,
                    'org_id': org_id,
                })

        # Associer les audits de ce partner à la nouvelle organisation
        if _column_exists(conn, 'audits', 'partner_id'):
            conn.execute(sa.text(
                "UPDATE audits SET organization_id = :org_id WHERE partner_id = :partner_id"
            ), {'org_id': org_id, 'partner_id': str(p.id)})

    # 6. Supprimer l'ancienne contrainte FK et colonne partner_id
    if _column_exists(conn, 'audits', 'partner_id'):
        try:
            op.drop_constraint('audits_partner_id_fkey', 'audits', type_='foreignkey')
        except Exception:
            pass
        op.drop_column('audits', 'partner_id')

    # 7. Rendre organization_id NOT NULL
    op.alter_column('audits', 'organization_id', nullable=False)

    # 8. Supprimer la table partners
    op.drop_table('partners')


def downgrade() -> None:
    # Recreate partners table and restore partner_id on audits
    op.create_table(
        'partners',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('company_name', sa.String(255), nullable=False),
        sa.Column('brand_primary_color', sa.String(7), server_default='#1B5E20'),
        sa.Column('brand_secondary_color', sa.String(7), server_default='#2E7D32'),
        sa.Column('contact_name', sa.String(255), nullable=True),
        sa.Column('contact_phone', sa.String(50), nullable=True),
        sa.Column('stripe_customer_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.add_column('audits', sa.Column(
        'partner_id', postgresql.UUID(as_uuid=True),
        sa.ForeignKey('partners.id'), nullable=True
    ))
    op.drop_column('audits', 'organization_id')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    op.drop_table('organizations')
