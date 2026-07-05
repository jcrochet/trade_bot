class Strategy:
    def __init__(
        self, name: str,
        interval: int,
        order_type: str,
        pair: str,
        units: float,
        take_profit: float,
        stop_loss: float
    ):
        self.name = name
        self.interval = interval
        # either long or short
        self.order_type = order_type
        self.pair = pair
        self.units = units
        self.take_profit = take_profit
        self.stop_loss = stop_loss