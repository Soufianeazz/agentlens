from sqlalchemy import JSON, Boolean, Column, Float, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class BudgetAlert(Base):
    __tablename__ = "budget_alerts"

    id = Column(String, primary_key=True, default="default")
    daily_budget_usd = Column(Float, nullable=False)
    webhook_url = Column(String, nullable=True)
    email = Column(String, nullable=True)
    triggered_today = Column(Boolean, default=False)
    last_triggered = Column(Float, nullable=True)  # unix epoch


class Request(Base):
    __tablename__ = "requests"

    id = Column(String, primary_key=True)
    input = Column(Text, nullable=False)
    output = Column(Text, nullable=False)
    prompt = Column(Text, nullable=False)
    model = Column(String, nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
    timestamp = Column(Float, nullable=False, index=True)

    evaluation = relationship("Evaluation", back_populates="request", uselist=False)


class Evaluation(Base):
    __tablename__ = "evaluations"

    request_id = Column(String, ForeignKey("requests.id"), primary_key=True)
    quality_score = Column(Float, nullable=False, index=True)
    hallucination_score = Column(Float, nullable=False)
    flags = Column(JSON, default=list)
    score_explanation = Column(Text)

    request = relationship("Request", back_populates="evaluation")
