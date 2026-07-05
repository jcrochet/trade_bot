import requests
from bs4 import BeautifulSoup
import traceback
import logging
from app.db_setup import engine, ExchangeRate
from app.scraper_setup import get_random_string_from_file
from sqlalchemy.orm import Session
from datetime import datetime
import sys
from dotenv import load_dotenv
import os

load_dotenv()

# set up logging
logger = logging.getLogger(__name__)

# default notification target
notification_target = os.getenv("NOTIFICATION_TARGET")


def get_aggregate_price(
    pair: str, notification_target: str = notification_target
) -> float:
    logger.info(f"Retrieving aggregate exchange rate for {pair}.")
    exchange_rates = []
    # scrape exchange rates from sources
    exchange_rates.append(scrape_investing_com(pair, notification_target))
    exchange_rates.append(scrape_google_finance(pair, notification_target))
    exchange_rates.append(scrape_exchange_rates_org(pair, notification_target))
    logger.debug(f"Scraped rates are {exchange_rates}")

    # get average of all scraped exchange rates
    valid_rates = [
        exchange_rate for exchange_rate in exchange_rates if exchange_rate is not None
    ]
    logger.debug(f"Valid rates are {valid_rates}")
    average_exchange_rate = round(sum(valid_rates) / len(valid_rates), 4)
    logger.info(f"Aggregate exchange rate is {average_exchange_rate}.")
    return average_exchange_rate


def enter_exchange_rate_into_db(
    pair: str, notification_target: str = notification_target
):
    # check to make sure pair string is formatted correctly
    if "/" not in pair:
        logger.error(
            f"{pair} is not formatted correctly. Make sure the symbols are separated by a '/'."
        )
        sys.exit(1)

    exchange_rate = get_aggregate_price(pair, notification_target)

    # add scraped exchange rate for pair to database
    with Session(engine) as session:
        logger.info(f"Entering exchange rate for {pair} into database.")
        new_exchange_rate = ExchangeRate(
            pair=pair, time=datetime.now(), exchange_rate=exchange_rate
        )
        session.add(new_exchange_rate)
        session.commit()
        logger.info("Done!")


def scrape_investing_com(pair: str, notification_target: str) -> float:
    # format pair as asset1-asset2 and build url
    pair = "-".join(pair.split("/")).lower()
    url = f"https://www.investing.com/currencies/{pair}"
    element_criteria = "div[data-test='instrument-price-last']"
    site_name = "Investing.com"
    try:
        exchange_rate = standard_exchange_rate_extract(
            url, element_criteria, site_name, notification_target
        )
        if exchange_rate is not None:
            exchange_rate = float(exchange_rate)
            return exchange_rate
        else:
            raise ValueError(f"{site_name} did not return an exchange rate.")
    except Exception:
        logger.debug(traceback.format_exc())
        return


def scrape_google_finance(pair: str, notification_target: str) -> float:
    # format pair as ASSET1-ASSET2 and build url
    pair = "-".join(pair.split("/")).upper()
    url = f"https://www.google.com/finance/quote/{pair}"
    element_criteria = "div[class='YMlKec fxKbKc']"
    site_name = "Google Finance"
    try:
        exchange_rate = standard_exchange_rate_extract(
            url, element_criteria, site_name, notification_target
        )
        if exchange_rate is not None:
            exchange_rate = float(exchange_rate)
            return exchange_rate
        else:
            raise ValueError(f"{site_name} did not return an exchange rate.")
    except Exception:
        logger.debug(traceback.format_exc())
        return


def scrape_exchange_rates_org(pair: str, notification_target: str) -> float:
    # format pair as asset1-asset2 and build url
    pair = "-".join(pair.split("/")).lower()
    url = f"https://www.exchange-rates.org/converter/{pair}"
    element_criteria = "span[class='rate-to']"
    site_name = "Exchange-Rates.org"
    try:
        exchange_rate = standard_exchange_rate_extract(
            url, element_criteria, site_name, notification_target
        )
        if exchange_rate is not None:
            # this site returns in the format 0.8746 EUR, so cut out the currency symbol
            exchange_rate = exchange_rate.split(" ")[0]
            exchange_rate = float(exchange_rate)
            return exchange_rate
        else:
            raise ValueError(f"{site_name} did not return an exchange rate.")
    except Exception:
        logger.debug(traceback.format_exc())
        return


def extract_soup(url: str) -> BeautifulSoup:
    headers = {
        "User-Agent": get_random_string_from_file("user-agent"),
    }
    proxies = {"http": f"http://{get_random_string_from_file('proxy')}"}
    logger.debug(f"Using http headers: {headers}")
    logger.debug(f"Using proxy: {proxies}")

    # scrape url
    html = requests.get(url, proxies=proxies, headers=headers).text
    soup = BeautifulSoup(html, "html.parser")
    return soup


def standard_exchange_rate_extract(
    url: str, element_criteria: str, site_name: str, notification_target: str
) -> str:
    soup = extract_soup(url)
    try:
        # extract exchange rate
        exchange_rate_elem = soup.select(element_criteria)
        try:
            exchange_rate = exchange_rate_elem[0].text
        except IndexError:
            return
        logger.debug(f"{site_name} exchange rate: {exchange_rate}.")
        return exchange_rate

    except Exception as e:
        logging.error(traceback.format_exc())
        requests.post(
            notification_target,
            data=f"an error occurred on {site_name} scraper. See log for details.",
        )
        return


# # for testing
# if __name__ == "__main__":
#     pair = "USD/EUR"
#     exchange_rate = enter_exchange_rate_into_db(pair)
