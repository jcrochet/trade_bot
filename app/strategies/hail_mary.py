# THIS IS AN EXAMPLE STRATEGY
# a strategy needs an evaluate_price function which will accept a DataFrame as an argument
# the DataFrame should have rows that represent datetime values and columns giving asset price
# the evaluate_price function will read the dataframe and determine if a buy, sell, or hold is done
# the strategy will also have an interval representing how often the strategy runs
# the strategy needs to return a strategy object
import pandas as pd
from types import MethodType
from app.strategy_base import Strategy
import logging

logger = logging.getLogger(__name__)

strategy = Strategy(
    name=__name__,
    interval=60,
    order_type="long",
    pair="USD/EUR",
    units=10000,
    take_profit=0.4,
    stop_loss=0.2,
)


def check_for_signal(self, price_data: pd.DataFrame) -> bool:
    if len(price_data) < 4:
        logger.debug("Need to download more data before running strategy.")
        return True
    latest_prices = price_data.tail(4).iloc

    logger.debug(f"Latest prices: {latest_prices}")

    if (
        latest_prices[0]["rate"] > latest_prices[1]["rate"]
        and latest_prices[1]["rate"] > latest_prices[2]["rate"]
        and latest_prices[2]["rate"] > latest_prices[3]["rate"]
    ):
        logger.debug("Enter signal received!")
        return False
    else:
        logger.debug("Enter signal not received. Waiting...")
        return True


def evaluate_price(self, take_profit_price, stop_loss_price, price_data: pd.DataFrame):
    latest_data = price_data.tail(1)
    latest_rate = latest_data["rate"].iloc[0]
    latest_time = latest_data["time"].iloc[0].strftime(r"%m/%d/%Y %H:%M:%S")

    logger.info(f"Latest exchange rate is {latest_rate} at {latest_time}.")
    logger.debug(f"Take Profit: {take_profit_price:.4f}")
    logger.debug(f"Stop Loss: {stop_loss_price:.4f}")

    if latest_rate >= take_profit_price or latest_rate <= stop_loss_price:
        logger.debug("Sending close signal.")
        return "close"
    else:
        logger.debug("Sending hold signal.")
        return "hold"


# add evaluate_price method to the Strategy class
strategy.evaluate_price = MethodType(evaluate_price, strategy)
strategy.check_for_signal = MethodType(check_for_signal, strategy)
