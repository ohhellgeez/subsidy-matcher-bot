import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Region, Company, SupportMeasure, MeasureRequirement, Document

DATABASE_URL = (
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER', 'myuser')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'mypassword')}"
    f"@{os.getenv('POSTGRES_HOST', 'db')}:{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB', 'max_db')}"
)

engine = create_engine(DATABASE_URL)

def load_json(filename):
    filepath = os.path.join(os.path.dirname(__file__), 'data', filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def seed_data():
    with Session(engine) as session:
        print("Загрузка регионов...")
        regions_data = load_json('regions.json')
        for r_data in regions_data:
            if not session.query(Region).filter_by(okato=r_data['okato']).first():
                region = Region(**r_data)
                session.add(region)
        session.commit()

        print("Загрузка компаний...")
        companies_data = load_json('companies.json')
        for c_data in companies_data:
            if not session.query(Company).filter_by(inn=c_data['inn']).first():
                region = session.query(Region).filter_by(okato=c_data.pop('region_okato')).first()
                if region:
                    company = Company(**c_data, region_id=region.id)
                    session.add(company)
        session.commit()

        print("Загрузка мер поддержки...")
        measures_data = load_json('measures.json')
        for m_data in measures_data:
            if not session.query(SupportMeasure).filter_by(id=m_data['id']).first():
                reqs_data = m_data.pop('requirements', {})
                docs_data = m_data.pop('documents', [])
                
                measure = SupportMeasure(**m_data)
                
                requirement = MeasureRequirement(**reqs_data, measure_id=measure.id)
                measure.requirements = requirement
                
                for d_data in docs_data:
                    doc = Document(**d_data, measure_id=measure.id)
                    measure.documents.append(doc)
                
                session.add(measure)
        session.commit()
        print("База успешно заполнена тестовыми данными!")

if __name__ == "__main__":
    seed_data()