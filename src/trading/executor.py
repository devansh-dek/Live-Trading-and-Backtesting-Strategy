class TradeExecutor:
    def __init__(self, exchange):
        self.exchange = exchange

    def execute(self, signal):
        if signal == "BUY":
            # calculate amount
            self.exchange.place_order("BUY", 0.001)
