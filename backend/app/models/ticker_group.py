from sqlalchemy import Column, String
from app.database import Base


class TickerGroup(Base):
    __tablename__ = "ticker_groups"
    ticker = Column(String, primary_key=True)
    group_name = Column(String, nullable=False)
