import pytest
from deep_research.db import get_engine, create_tables, upsert_opportunity, Opportunity
from sqlalchemy.orm import sessionmaker

@pytest.fixture
def session():
    engine = get_engine(use_sqlite_memory=True)
    create_tables(engine)
    Session = sessionmaker(bind=engine, future=True)
    sess = Session()
    yield sess
    sess.close()

def test_upsert_insert_and_update(session):
    item = {
        "id": "testid1",
        "source_id": "source1",
        "title": "First",
        "description": "Desc",
        "deadline": None,
        "opportunity_type": "financement",
        "sector": "agri",
        "stage": None,
        "amount": 1000,
        "source_url": "http://example.com/op/1",
        "scraped_at": None,
        "updated_at": None,
    }
    upsert_opportunity(session, item)
    assert session.query(Opportunity).count() == 1

    # Update
    item2 = item.copy()
    item2["title"] = "Updated Title"
    upsert_opportunity(session, item2)
    assert session.query(Opportunity).count() == 1
    row = session.query(Opportunity).filter_by(source_url="http://example.com/op/1").first()
    assert row.title == "Updated Title"