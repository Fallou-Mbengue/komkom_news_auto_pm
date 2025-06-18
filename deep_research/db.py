import os
import uuid
import enum
import datetime
from sqlalchemy import (
    create_engine, Column, String, Date, Enum, Numeric, Text,
    TIMESTAMP, func, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine.url import URL

Base = declarative_base()


class OpportunityType(enum.Enum):
    financement = "financement"
    accompagnement = "accompagnement"


class Opportunity(Base):
    __tablename__ = "opportunities"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_id = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=False)
    deadline = Column(Date, nullable=True)
    opportunity_type = Column(Enum(OpportunityType), nullable=False)
    sector = Column(Text, nullable=True)
    stage = Column(Text, nullable=True)
    amount = Column(Numeric, nullable=True)
    source_url = Column(Text, unique=True, nullable=False)
    scraped_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('source_url', name='_source_url_uc'),
    )


def get_engine(echo=False, use_sqlite_memory=False):
    if use_sqlite_memory:
        return create_engine("sqlite:///:memory:", echo=echo, future=True)
    db_url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        host=os.environ.get("DB_HOST"),
        port=os.environ.get("DB_PORT"),
        database=os.environ.get("DB_NAME"),
    )
    return create_engine(db_url, echo=echo, future=True)


def create_tables(engine=None):
    if engine is None:
        engine = get_engine()
    Base.metadata.create_all(engine)


def upsert_opportunity(session, item):
    """Upsert logic based on source_url SHA256 uniqueness."""
    from sqlalchemy import select, update
    now = datetime.datetime.utcnow()
    existing = session.execute(
        select(Opportunity).where(Opportunity.source_url == item['source_url'])
    ).scalar_one_or_none()

    if existing:
        changed = False
        fields_to_update = [
            'title', 'description', 'deadline', 'opportunity_type',
            'sector', 'stage', 'amount'
        ]
        for field in fields_to_update:
            if getattr(existing, field) != item.get(field):
                setattr(existing, field, item.get(field))
                changed = True
        if changed:
            existing.updated_at = now
        session.commit()
        return existing.id
    else:
        opp = Opportunity(
            id=item.get('id', str(uuid.uuid4())),
            source_id=item['source_id'],
            title=item['title'],
            description=item['description'],
            deadline=item.get('deadline'),
            opportunity_type=item['opportunity_type'],
            sector=item.get('sector'),
            stage=item.get('stage'),
            amount=item.get('amount'),
            source_url=item['source_url'],
            scraped_at=item.get('scraped_at', now),
            updated_at=now,
        )
        session.add(opp)
        session.commit()
        return opp.id

if __name__ == "__main__":
    # For Makefile migrate
    engine = get_engine()
    create_tables(engine)
    print("DB migration complete.")