from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    String, Text, DateTime, Integer, Float, Boolean, ForeignKey,
    CheckConstraint, UniqueConstraint, func
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class SupportMeasure(Base):
    __tablename__ = "support_measures"

    id: Mapped[str] = mapped_column(String, primary_key=True, comment="Внутренний ID")
    id_form: Mapped[Optional[str]] = mapped_column(String, default='0', server_default='0')
    active: Mapped[int] = mapped_column(Integer, default=1, server_default='1')
    name: Mapped[str] = mapped_column(String(150))
    preview: Mapped[Optional[str]] = mapped_column(String(250))
    short_description: Mapped[Optional[str]] = mapped_column(Text)
    full_description: Mapped[Optional[str]] = mapped_column(Text)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    support_type: Mapped[Optional[int]] = mapped_column(Integer)
    support_count: Mapped[Optional[int]] = mapped_column(Integer)
    support_amount_from: Mapped[Optional[int]] = mapped_column(Integer)
    support_amount_till: Mapped[Optional[int]] = mapped_column(Integer)
    recipient_category: Mapped[Optional[str]] = mapped_column(String, comment="micro, small, medium")
    recipient_description: Mapped[Optional[str]] = mapped_column(Text, comment="Подробное текстовое описание получателей")
    source_name: Mapped[Optional[str]] = mapped_column(String(100), comment="Название источника (МСП.РФ, ФРП, Минсельхоз)")
    source_url: Mapped[Optional[str]] = mapped_column(String, comment="Прямая ссылка на официальную страницу меры")

    requirements: Mapped["MeasureRequirement"] = relationship(back_populates="measure", cascade="all, delete")
    documents: Mapped[List["Document"]] = relationship(back_populates="measure", cascade="all, delete")

    __table_args__ = (
        CheckConstraint("active IN (0, 1)", name="chk_measure_active"),
        CheckConstraint("end_date >= start_date", name="chk_measure_dates"),
        CheckConstraint("support_amount_from >= 0 AND support_amount_till >= 0", name="chk_measure_amounts"),
    )


class MeasureRequirement(Base):
    __tablename__ = "measure_requirements"

    measure_id: Mapped[str] = mapped_column(String, ForeignKey("support_measures.id", ondelete="CASCADE"), primary_key=True, comment="Связь 1 к 1 с мерой поддержки")
    opf: Mapped[Optional[str]] = mapped_column(String, comment="ОПФ: individual, legal, self и т.д. (массив)")
    okwed: Mapped[Optional[str]] = mapped_column(String, comment="Допустимые ОКВЭДы (массив)")
    not_okwed: Mapped[Optional[str]] = mapped_column(String, comment="Недопустимые ОКВЭДы (массив)")
    min_empl_amount: Mapped[Optional[int]] = mapped_column(Integer, comment="Мин. кол-во сотрудников")
    max_empl_amount: Mapped[Optional[int]] = mapped_column(Integer, comment="Макс. кол-во сотрудников")
    min_exist_term: Mapped[Optional[int]] = mapped_column(Integer, comment="Мин. срок ведения бизнеса (в месяцах)")
    okato: Mapped[Optional[str]] = mapped_column(String, default='0', server_default='0', comment="Ограничения по ОКАТО (0 - вся РФ)")
    ukep: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, server_default='false', comment="Требование наличия УКЭП (ЭЦП)")
    scoring: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, server_default='false', comment="Требование прохождения скоринга")

    measure: Mapped["SupportMeasure"] = relationship(back_populates="requirements")

    __table_args__ = (
        CheckConstraint("min_empl_amount >= 0 AND max_empl_amount >= min_empl_amount", name="chk_req_employees"),
        CheckConstraint("min_exist_term >= 0", name="chk_req_exist_term"),
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    measure_id: Mapped[str] = mapped_column(String, ForeignKey("support_measures.id", ondelete="CASCADE"), comment="Связь многие-к-одному")
    link: Mapped[str] = mapped_column(String, comment="Ссылка на документ на внешнем ресурсе")
    type: Mapped[Optional[str]] = mapped_column(String(10), comment="Формат: pdf, docx, jpg")
    size: Mapped[Optional[float]] = mapped_column(Float, comment="Размер в килобайтах")
    name: Mapped[str] = mapped_column(String, comment="Имя документа с реквизитами")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="Описание")

    measure: Mapped["SupportMeasure"] = relationship(back_populates="documents")

    __table_args__ = (
        CheckConstraint("size > 0", name="chk_doc_size"),
        UniqueConstraint("measure_id", "link", name="uq_measure_link"),
    )


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    okato: Mapped[str] = mapped_column(String(20), unique=True, comment="Код ОКАТО (например 01)")
    code: Mapped[str] = mapped_column(String(10), unique=True, comment="ISO код (например RU-ALT)")
    name: Mapped[str] = mapped_column(String, unique=True, comment="Название региона")
    district: Mapped[Optional[str]] = mapped_column(String, comment="Федеральный округ")


class Company(Base):
    __tablename__ = "companies"

    inn: Mapped[str] = mapped_column(String(12), primary_key=True, comment="ИНН компании (моковые данные)")
    name: Mapped[str] = mapped_column(String, comment="Название ООО/ИП")
    opf: Mapped[str] = mapped_column(String, comment="ОПФ компании")
    okwed: Mapped[str] = mapped_column(String(10), comment="Основной ОКВЭД")
    employees_count: Mapped[Optional[int]] = mapped_column(Integer, comment="Кол-во сотрудников")
    exist_term_months: Mapped[Optional[int]] = mapped_column(Integer, comment="Возраст бизнеса (мес)")
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("regions.id"), comment="Ссылка на регион (ОКАТО)")

    __table_args__ = (
        CheckConstraint("length(inn) IN (10, 12)", name="chk_company_inn_length"),
        CheckConstraint("employees_count >= 0 AND exist_term_months >= 0", name="chk_company_metrics"),
        CheckConstraint("opf IN ('individual', 'legal', 'physical', 'self', 'selfindividual')", name="chk_company_opf"),
        CheckConstraint("trim(name) <> ''", name="chk_company_name_not_empty"),
    )
