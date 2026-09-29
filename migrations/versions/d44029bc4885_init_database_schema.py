"""Init database schema

Revision ID: d44029bc4885
Revises:
Create Date: 2026-09-26 22:00:21.809909

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd44029bc4885'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'support_measures',
        sa.Column('id', sa.String(), nullable=False, comment='Внутренний ID меры поддержки'),
        sa.Column('id_form', sa.String(), nullable=True, server_default='0', comment='ID формы предоставления (0 если универсальная)'),
        sa.Column('active', sa.Integer(), nullable=False, server_default='1', comment='1 - активна, 0 - убрать с платформы'),
        sa.Column('name', sa.String(length=150), nullable=False, comment='Наименование без формулировок НПА'),
        sa.Column('preview', sa.String(length=250), nullable=True, comment='Краткий анонс для списка'),
        sa.Column('short_description', sa.Text(), nullable=True, comment='Краткое описание для карточки'),
        sa.Column('full_description', sa.Text(), nullable=True, comment='Полное описание (с HTML тегами)'),
        sa.Column('start_date', sa.DateTime(), nullable=True, comment='Дата начала приема заявок (ISO 8601)'),
        sa.Column('end_date', sa.DateTime(), nullable=True, comment='Дата окончания приема заявок (ISO 8601)'),
        sa.Column('support_type', sa.Integer(), nullable=True, comment='Форма поддержки (ID из справочника)'),
        sa.Column('support_count', sa.Integer(), nullable=True, comment='Лимит оказания меры на заявителя'),
        sa.Column('support_amount_from', sa.Integer(), nullable=True, comment='Размер поддержки ОТ (руб)'),
        sa.Column('support_amount_till', sa.Integer(), nullable=True, comment='Размер поддержки ДО (руб)'),
        sa.Column('recipient_category', sa.String(), nullable=True, comment='Категории: micro, small, medium, other (массив)'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('active IN (0, 1)', name='chk_measure_active'),
        sa.CheckConstraint('end_date >= start_date', name='chk_measure_dates'),
        sa.CheckConstraint('support_amount_from >= 0 AND support_amount_till >= 0 AND support_amount_till >= support_amount_from', name='chk_measure_amounts'),
        sa.CheckConstraint('support_count >= 0', name='chk_measure_count'),
        sa.CheckConstraint("trim(name) <> ''", name='chk_measure_name_not_empty'),
    )

    op.create_table(
        'regions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('okato', sa.String(length=20), nullable=False, comment='Код ОКАТО (например 01)'),
        sa.Column('code', sa.String(length=10), nullable=False, comment='ISO код (например RU-ALT)'),
        sa.Column('name', sa.String(), nullable=False, comment='Название региона'),
        sa.Column('district', sa.String(), nullable=True, comment='Федеральный округ'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('okato', name='uq_region_okato'),
        sa.UniqueConstraint('code', name='uq_region_code'),
        sa.UniqueConstraint('name', name='uq_region_name'),
    )

    op.create_table(
        'measure_requirements',
        sa.Column('measure_id', sa.String(), nullable=False, comment='Связь 1 к 1 с мерой поддержки'),
        sa.Column('opf', sa.String(), nullable=True, comment='ОПФ: individual, legal, self и т.д. (массив)'),
        sa.Column('okwed', sa.String(), nullable=True, comment='Допустимые ОКВЭДы (массив)'),
        sa.Column('not_okwed', sa.String(), nullable=True, comment='Недопустимые ОКВЭДы (массив)'),
        sa.Column('min_empl_amount', sa.Integer(), nullable=True, comment='Мин. кол-во сотрудников'),
        sa.Column('max_empl_amount', sa.Integer(), nullable=True, comment='Макс. кол-во сотрудников'),
        sa.Column('min_exist_term', sa.Integer(), nullable=True, comment='Мин. срок ведения бизнеса (в месяцах)'),
        sa.Column('okato', sa.String(), nullable=True, server_default='0', comment='Ограничения по ОКАТО (0 - вся РФ)'),
        sa.Column('ukep', sa.Boolean(), nullable=True, server_default='false', comment='Требование наличия УКЭП (ЭЦП)'),
        sa.Column('scoring', sa.Boolean(), nullable=True, server_default='false', comment='Требование прохождения скоринга'),
        sa.PrimaryKeyConstraint('measure_id'),
        sa.ForeignKeyConstraint(['measure_id'], ['support_measures.id'], name='fk_measure_requirements_measure_id', ondelete='CASCADE'),
        sa.CheckConstraint('min_empl_amount >= 0 AND max_empl_amount >= min_empl_amount', name='chk_req_employees'),
        sa.CheckConstraint('min_exist_term >= 0', name='chk_req_exist_term'),
    )

    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('measure_id', sa.String(), nullable=False, comment='Связь многие-к-одному'),
        sa.Column('link', sa.String(), nullable=False, comment='Ссылка на документ на внешнем ресурсе'),
        sa.Column('type', sa.String(length=10), nullable=True, comment='Формат: pdf, docx, jpg'),
        sa.Column('size', sa.Float(), nullable=True, comment='Размер в килобайтах'),
        sa.Column('name', sa.String(), nullable=False, comment='Имя документа с реквизитами'),
        sa.Column('description', sa.Text(), nullable=True, comment='Описание'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['measure_id'], ['support_measures.id'], name='fk_documents_measure_id', ondelete='CASCADE'),
        sa.CheckConstraint('size > 0', name='chk_doc_size'),
        sa.UniqueConstraint('measure_id', 'link', name='uq_measure_link'),
    )

    op.create_table(
        'companies',
        sa.Column('inn', sa.String(length=12), nullable=False, comment='ИНН компании (моковые данные)'),
        sa.Column('name', sa.String(), nullable=False, comment='Название ООО/ИП'),
        sa.Column('opf', sa.String(), nullable=False, comment='ОПФ компании'),
        sa.Column('okwed', sa.String(length=10), nullable=False, comment='Основной ОКВЭД'),
        sa.Column('employees_count', sa.Integer(), nullable=True, comment='Кол-во сотрудников'),
        sa.Column('exist_term_months', sa.Integer(), nullable=True, comment='Возраст бизнеса (мес)'),
        sa.Column('region_id', sa.Integer(), nullable=False, comment='Ссылка на регион (ОКАТО)'),
        sa.PrimaryKeyConstraint('inn'),
        sa.ForeignKeyConstraint(['region_id'], ['regions.id'], name='fk_companies_region_id'),
        sa.CheckConstraint('length(inn) IN (10, 12)', name='chk_company_inn_length'),
        sa.CheckConstraint('employees_count >= 0 AND exist_term_months >= 0', name='chk_company_metrics'),
        sa.CheckConstraint("opf IN ('individual', 'legal', 'physical', 'self', 'selfindividual')", name='chk_company_opf'),
        sa.CheckConstraint("trim(name) <> ''", name='chk_company_name_not_empty'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('companies')
    op.drop_table('documents')
    op.drop_table('measure_requirements')
    op.drop_table('regions')
    op.drop_table('support_measures')
