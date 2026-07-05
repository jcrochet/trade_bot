from app.price_scraper import get_aggregate_price
from app.db_setup import engine, TradeOrder
from datetime import datetime
from sqlalchemy.orm import Session
import traceback
import logging
import os

# set up logging
logger = logging.getLogger(__name__)

# take profit and stop loss are strings so user
# can pass % for dynamic exit levels
def open_order(
    order_type: str,
    pair: str, 
    units: float, 
    take_profit: float,
    stop_loss: float,
    strategy: str
) -> int:

    # scrape exchange rate at time of open
    open_price = get_aggregate_price(pair)

    logger.info(f"Received {order_type} order for {units} units of {pair} using {strategy.split('.')[-1]} strategy.")
    # if passed a percent for exit level, calculate the exit level
    # if "%" in take_profit:
    #     take_profit = float(take_profit.replace("%", ""))
    take_profit = set_exit_level(order_type, "take profit", open_price, take_profit)

    # if "%" in stop_loss:
    #     stop_loss = float(stop_loss.replace("%", ""))
    stop_loss = set_exit_level(order_type, "stop loss", open_price, stop_loss)

    # enter order into database
    new_order = TradeOrder(
        order_type=order_type,
        pair=pair,
        units=units,
        time_opened=datetime.now(),
        open_price=open_price,
        take_profit=take_profit,
        stop_loss=stop_loss,
        strategy=strategy
    )

    with Session(engine) as session:
        try:
            session.add(new_order)
            session.commit()
            logger.info(f"Entered order into database successfully!")
            return new_order.order_id
        except Exception as e:
            logging.error(traceback.format_exc())
            return


def set_exit_level(
    order_type: str,
    exit_type: str,
    open_price: float, 
    exit_percentage: float
) -> float:   
    if (order_type == "long" and exit_type == "stop loss") or (order_type == "short" and exit_type == "take profit"):
        exit_level =  open_price * (1 - exit_percentage / 100)
    elif order_type == "short" and exit_type == "stop loss" or (order_type == "long" and exit_type == "take profit"):
        exit_level =  open_price * (1 + exit_percentage / 100)
    logger.debug(f"Set {exit_type} to {exit_level:.4f}")
    return exit_level


def close_order(order_id: int):
    with Session(engine) as session:
        order = session.query(TradeOrder).filter_by(order_id=order_id).scalar()
        pair = order.pair
        # add close time and price to the order with order_id
        order.time_closed = datetime.now()
        order.close_price = get_aggregate_price(pair)
        session.commit()

# for testing
if __name__ == "__main__":
    order_id = open_order(
        order_type="long",
        pair="USD/EUR",
        units=10000.00,
        take_profit="20%",
        stop_loss="10%",
        strategy="hail mary"
    )
    close_order(order_id)