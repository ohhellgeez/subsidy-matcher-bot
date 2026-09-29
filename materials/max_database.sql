CREATE TABLE "support_measures" (
  "id" varchar PRIMARY KEY,
  "id_form" varchar DEFAULT '0',
  "active" int NOT NULL DEFAULT 1,
  "name" varchar(150) NOT NULL,
  "preview" varchar(250),
  "short_description" text,
  "full_description" text,
  "start_date" timestamp,
  "end_date" timestamp,
  "support_type" int,
  "support_count" int,
  "support_amount_from" int,
  "support_amount_till" int,
  "recipient_category" varchar
);

CREATE TABLE "measure_requirements" (
  "measure_id" varchar PRIMARY KEY,
  "opf" varchar,
  "okwed" varchar,
  "not_okwed" varchar,
  "min_empl_amount" int,
  "max_empl_amount" int,
  "min_exist_term" int,
  "okato" varchar DEFAULT '0',
  "ukep" boolean DEFAULT false,
  "scoring" boolean DEFAULT false
);

CREATE TABLE "documents" (
  "id" serial PRIMARY KEY,
  "measure_id" varchar NOT NULL,
  "link" varchar NOT NULL,
  "type" varchar(10),
  "size" float,
  "name" varchar NOT NULL,
  "description" text
);

CREATE TABLE "regions" (
  "id" serial PRIMARY KEY,
  "okato" varchar(20) NOT NULL,
  "code" varchar(10) NOT NULL,
  "name" varchar NOT NULL,
  "district" varchar
);

CREATE TABLE "companies" (
  "inn" varchar(12) PRIMARY KEY,
  "name" varchar NOT NULL,
  "opf" varchar NOT NULL,
  "okwed" varchar(10) NOT NULL,
  "employees_count" int,
  "exist_term_months" int,
  "region_id" int NOT NULL
);

COMMENT ON COLUMN "support_measures"."id" IS 'Внутренний ID меры поддержки';
COMMENT ON COLUMN "support_measures"."id_form" IS 'ID формы предоставления (0 если универсальная)';
COMMENT ON COLUMN "support_measures"."active" IS '1 - активна, 0 - убрать с платформы';
COMMENT ON COLUMN "support_measures"."name" IS 'Наименование без формулировок НПА';
COMMENT ON COLUMN "support_measures"."preview" IS 'Краткий анонс для списка';
COMMENT ON COLUMN "support_measures"."short_description" IS 'Краткое описание для карточки';
COMMENT ON COLUMN "support_measures"."full_description" IS 'Полное описание (с HTML тегами)';
COMMENT ON COLUMN "support_measures"."start_date" IS 'Дата начала приема заявок (ISO 8601)';
COMMENT ON COLUMN "support_measures"."end_date" IS 'Дата окончания приема заявок (ISO 8601)';
COMMENT ON COLUMN "support_measures"."support_type" IS 'Форма поддержки (ID из справочника)';
COMMENT ON COLUMN "support_measures"."support_count" IS 'Лимит оказания меры на заявителя';
COMMENT ON COLUMN "support_measures"."support_amount_from" IS 'Размер поддержки ОТ (руб)';
COMMENT ON COLUMN "support_measures"."support_amount_till" IS 'Размер поддержки ДО (руб)';
COMMENT ON COLUMN "support_measures"."recipient_category" IS 'Категории: micro, small, medium, other (массив)';

COMMENT ON COLUMN "measure_requirements"."measure_id" IS 'Связь 1 к 1 с мерой поддержки';
COMMENT ON COLUMN "measure_requirements"."opf" IS 'ОПФ: individual, legal, self и т.д. (массив)';
COMMENT ON COLUMN "measure_requirements"."okwed" IS 'Допустимые ОКВЭДы (массив)';
COMMENT ON COLUMN "measure_requirements"."not_okwed" IS 'Недопустимые ОКВЭДы (массив)';
COMMENT ON COLUMN "measure_requirements"."min_empl_amount" IS 'Мин. кол-во сотрудников';
COMMENT ON COLUMN "measure_requirements"."max_empl_amount" IS 'Макс. кол-во сотрудников';
COMMENT ON COLUMN "measure_requirements"."min_exist_term" IS 'Мин. срок ведения бизнеса (в месяцах)';
COMMENT ON COLUMN "measure_requirements"."okato" IS 'Ограничения по ОКАТО (0 - вся РФ)';
COMMENT ON COLUMN "measure_requirements"."ukep" IS 'Требование наличия УКЭП (ЭЦП)';
COMMENT ON COLUMN "measure_requirements"."scoring" IS 'Требование прохождения скоринга';

COMMENT ON COLUMN "documents"."measure_id" IS 'Связь многие-к-одному';
COMMENT ON COLUMN "documents"."link" IS 'Ссылка на документ на внешнем ресурсе';
COMMENT ON COLUMN "documents"."type" IS 'Формат: pdf, docx, jpg';
COMMENT ON COLUMN "documents"."size" IS 'Размер в килобайтах';
COMMENT ON COLUMN "documents"."name" IS 'Имя документа с реквизитами';
COMMENT ON COLUMN "documents"."description" IS 'Описание';

COMMENT ON COLUMN "regions"."okato" IS 'Код ОКАТО (например 01)';
COMMENT ON COLUMN "regions"."code" IS 'ISO код (например RU-ALT)';
COMMENT ON COLUMN "regions"."name" IS 'Название региона';
COMMENT ON COLUMN "regions"."district" IS 'Федеральный округ';

COMMENT ON COLUMN "companies"."inn" IS 'ИНН компании (моковые данные)';
COMMENT ON COLUMN "companies"."name" IS 'Название ООО/ИП';
COMMENT ON COLUMN "companies"."opf" IS 'ОПФ компании';
COMMENT ON COLUMN "companies"."okwed" IS 'Основной ОКВЭД';
COMMENT ON COLUMN "companies"."employees_count" IS 'Кол-во сотрудников';
COMMENT ON COLUMN "companies"."exist_term_months" IS 'Возраст бизнеса (мес)';
COMMENT ON COLUMN "companies"."region_id" IS 'Ссылка на регион (ОКАТО)';

ALTER TABLE "support_measures" 
  ADD CONSTRAINT "chk_measure_active" CHECK ("active" IN (0, 1)),
  ADD CONSTRAINT "chk_measure_dates" CHECK ("end_date" >= "start_date"),
  ADD CONSTRAINT "chk_measure_amounts" CHECK (
    "support_amount_from" >= 0 AND 
    "support_amount_till" >= 0 AND
    "support_amount_till" >= "support_amount_from"
  ),
  ADD CONSTRAINT "chk_measure_count" CHECK ("support_count" >= 0),
  ADD CONSTRAINT "chk_measure_name_not_empty" CHECK (trim("name") <> '');

ALTER TABLE "measure_requirements" 
  ADD CONSTRAINT "chk_req_employees" CHECK (
    "min_empl_amount" >= 0 AND 
    "max_empl_amount" >= "min_empl_amount"
  ),
  ADD CONSTRAINT "chk_req_exist_term" CHECK ("min_exist_term" >= 0);

ALTER TABLE "documents" 
  ADD CONSTRAINT "chk_doc_size" CHECK ("size" > 0),
  ADD CONSTRAINT "uq_measure_link" UNIQUE ("measure_id", "link");

ALTER TABLE "regions" 
  ADD CONSTRAINT "uq_region_okato" UNIQUE ("okato"),
  ADD CONSTRAINT "uq_region_code" UNIQUE ("code"),
  ADD CONSTRAINT "uq_region_name" UNIQUE ("name");

ALTER TABLE "companies" 
  ADD CONSTRAINT "chk_company_inn_length" CHECK (length("inn") IN (10, 12)),
  ADD CONSTRAINT "chk_company_metrics" CHECK ("employees_count" >= 0 AND "exist_term_months" >= 0),
  ADD CONSTRAINT "chk_company_opf" CHECK ("opf" IN ('individual', 'legal', 'physical', 'self', 'selfindividual')),
  ADD CONSTRAINT "chk_company_name_not_empty" CHECK (trim("name") <> '');

ALTER TABLE "measure_requirements" 
  ADD CONSTRAINT "fk_measure_requirements_measure_id"
  FOREIGN KEY ("measure_id") REFERENCES "support_measures" ("id") ON DELETE CASCADE;

ALTER TABLE "documents" 
  ADD CONSTRAINT "fk_documents_measure_id"
  FOREIGN KEY ("measure_id") REFERENCES "support_measures" ("id") ON DELETE CASCADE;

ALTER TABLE "companies" 
  ADD CONSTRAINT "fk_companies_region_id"
  FOREIGN KEY ("region_id") REFERENCES "regions" ("id") DEFERRABLE INITIALLY IMMEDIATE;