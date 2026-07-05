from sqlalchemy import create_engine, Integer, String, Float, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
import os
from datetime import datetime

# create database connection string
db_user = os.getenv("POSTGRES_USER")
db_name = os.getenv("POSTGRES_DB")
db_pass = os.getenv("POSTGRES_PASSWORD")
engine = create_engine(f"postgresql+psycopg2://{db_user}:{db_pass}@db/{db_name}")


# create classes representing tables in the database
class Base(DeclarativeBase):
    pass


class ExchangeRate(Base):
    __tablename__ = "exchange_rate"
    rate_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pair: Mapped[str] = mapped_column(String(10))
    time: Mapped[datetime] = mapped_column(DateTime)
    exchange_rate: Mapped[float] = mapped_column(Float)


class TradeOrder(Base):
    __tablename__ = "trade_order"
    order_id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    order_type: Mapped[str] = mapped_column(String(5), nullable=False)
    pair: Mapped[str] = mapped_column(String(10), nullable=False)
    units: Mapped[float] = mapped_column(Float, nullable=False)
    time_opened: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    open_price: Mapped[float] = mapped_column(Float, nullable=False)
    take_profit: Mapped[float] = mapped_column(Float, nullable=False)
    stop_loss: Mapped[float] = mapped_column(Float, nullable=False)
    time_closed: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    close_price: Mapped[float] = mapped_column(Float, nullable=True)
    strategy: Mapped[str] = mapped_column(String, nullable=False)


if __name__ == "__main__":
    # create all declared classes if they don't already exist
    Base.metadata.create_all(bind=engine)
