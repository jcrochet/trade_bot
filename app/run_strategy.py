from app.price_scraper import get_aggregate_price, notification_target
from app.db_setup import engine, TradeOrder
import requests
import pandas as pd
from datetime import datetime
import sys
from app.order_manager import open_order, close_order
import importlib
import logging
import traceback
import time
from sqlalchemy.orm import Session

rates = []
times = []

logging.basicConfig(filename="app/logs/trade_bot.log", level=logging.DEBUG)
logger = logging.getLogger(__name__)

def load_strategy(strategy_name: str) -> Strategy:
    try:
        module =  importlib.import_module(f"app.strategies.{strategy_name}")
        return module.strategy
    except Exception:
        logging.error(traceback.format_exc())
        return


def run_strategy(pair: str, strategy: Strategy):
    waiting_for_signal = True
    while waiting_for_signal:
        rates.append(get_aggregate_price(pair))
        times.append(datetime.now())
        price_data = pd.DataFrame({
            "rate": rates,
            "time": times
        })
        waiting_for_signal = strategy.check_for_signal(price_data)
        time.sleep(strategy.interval)

    logger.debug(f"{strategy.name} loaded.")
    logger.debug(f"Order Type: {strategy.order_type}")
    logger.debug(f"Pair: {strategy.pair}")
    logger.debug(f"Number of Units: {strategy.units}")
    logger.debug(f"Take Profit Ratio: {strategy.take_profit}")
    logger.debug(f"Stop Loss Ratio: {strategy.stop_loss}")

    # open the order and get order_id
    order_id = open_order(
        strategy.order_type,
        strategy.pair,
        strategy.units,
        strategy.take_profit,
        strategy.stop_loss,
        strategy.name
    )
    logger.debug(f"Order ID is {order_id}")

    # get open price, take profit and stop loss from order
    # could also be returned by open_order?
    with Session(engine) as session:
        order = session.query(TradeOrder).filter_by(order_id=order_id).scalar()
        open_price = order.open_price
        take_profit = order.take_profit
        stop_loss = order.stop_loss
        units = order.units

    logger.debug(f"Opening price is {open_price}.")
    requests.post(notification_target, data=f"Entered trade at {open_price}.")

    while True:
        # wait interval between scrapes
        logger.debug(f"Waiting {strategy.interval} seconds.")
        time.sleep(strategy.interval)

        # scrape exchange rate and time scraped and add to lists
        rates.append(get_aggregate_price(pair))
        logger.debug(f"List of scraped rates: {rates}")
        times.append(datetime.now())
        logger.debug(f"List of times rates were scraped: {times}")

        # create dataframe for analysis
        price_data = pd.DataFrame({
            "rate": rates,
            "time": times
        })

        # close order if close signal is received
        signal = strategy.evaluate_price(take_profit, stop_loss, price_data)

        if signal == "close":
            logger.info("Getting closing price.")
            close_order(order_id)
            with Session(engine) as session:
                close_price = session.query(TradeOrder).filter_by(order_id=order_id).scalar().close_price
            profit = units * (close_price - open_price) / close_price
            logger.debug(f"Profit/Loss: {profit:.4f}")

            if profit > 0:
                msg = f"Trade completed with profit of {abs(profit)}."
            elif profit < 0:
                msg = f"Trade completed with loss of {abs(profit)}."
            requests.post(notification_target, data=msg)
            break



if __name__ == "__main__":
    pair: str = sys.argv[1]
    strategy: Strategy = load_strategy(sys.argv[2])
    while True:
        run_strategy(pair, strategy)
