class Trade:
    def __init__(self, trade_type, strike, price, option_type, stock_price=None):
        """
        Represents an option trade.

        Args:
           trade_type (str): "Buy" or "Sell".
           strike (float): Strike price of the option.
           price (float): Price at which the option was traded.
           option_type (str): "Call" or "Put".
           stock_price (float):  Current price of the stock.
        """
        self.trade_type = trade_type
        self.strike = strike
        self.price = price
        self.option_type = option_type
        self.stock_price = stock_price
        self.stop_loss = None

    def calculate_break_even(self):
        """
        Calculates the break-even point for the trade.

        Returns:
            float: Break-even price.
        """
        if self.option_type == "Call":
            if self.trade_type == "Buy":
                return self.strike + self.price
            else:  # Sell Call
                return self.strike + self.price
        else:  # Put
            if self.trade_type == "Buy":
                return self.strike - self.price
            else:
                return self.strike - self.price

    def calculate_max_profit(self):
        """
         Calculates the maximum profit for the trade.

         Returns:
              float: Maximum profit.
        """
        if self.option_type == "Call":
            if self.trade_type == "Buy":
                return float('inf')
            else:  # Sell Call
                return self.price
        else:  # Put
            if self.trade_type == "Buy":
                return self.strike - self.price
            else:  # Sell Put
                return self.price

    def calculate_max_loss(self):
        """
         Calculates the maximum loss for the trade.
         Returns:
              float: Maximum loss
        """
        if self.option_type == "Call":
            if self.trade_type == "Buy":
                return self.price
            else:  # Sell Call
                return float('inf')  # potentially unlimited
        else:  # Put
            if self.trade_type == "Buy":
                return self.price
            else:  # Sell Put
                return float('inf')  # potentially unlimited

    def calculate_profit_loss(self, current_stock_price):
        """
        Calculates the current profit/loss for the trade.

        Args:
            current_stock_price (float): Current stock price.

        Returns:
            float: Profit/Loss amount.
        """
        if not current_stock_price:
            return 0  # Unable to calculate P/L without a current stock price

        if self.option_type == "Call":
            if self.trade_type == "Buy":
                return max(0, current_stock_price - self.strike) - self.price
            else:  # Sell Call
                return min(0, self.strike - current_stock_price) + self.price
        else:  # Put
            if self.trade_type == "Buy":
                return max(0, self.strike - current_stock_price) - self.price
            else:  # Sell Put
                return min(0, current_stock_price - self.strike) + self.price

    def set_stop_loss(self, price):
        """
        Sets the stop loss price for the trade.

        Args:
            price (float): The stop-loss price.
        """
        self.stop_loss = price

    def get_trade_info(self):
        """
        Returns a dictionary with key info about the trade

        Returns:
             dict: Dictionary of relevant trade information
        """
        return {
            "type": self.trade_type,
            "strike": self.strike,
            "price": self.price,
            "option_type": self.option_type,
            "stop_loss": self.stop_loss,
            "breakeven": self.calculate_break_even()

        }

    def __str__(self):
        return f"{self.trade_type} {self.option_type} at {self.strike} for ${self.price}"


if __name__ == '__main__':
    # Test scenarios
    call_buy = Trade("Buy", 150, 5, "Call", 155)
    put_buy = Trade("Buy", 150, 5, "Put", 145)
    call_sell = Trade("Sell", 150, 5, "Call", 155)
    put_sell = Trade("Sell", 150, 5, "Put", 145)

    print(f"Call Buy Break Even: {call_buy.calculate_break_even()}")  # Should be 155
    print(f"Put Buy Break Even: {put_buy.calculate_break_even()}")  # Should be 145
    print(f"Call Sell Break Even: {call_sell.calculate_break_even()}")  # Should be 155
    print(f"Put Sell Break Even: {put_sell.calculate_break_even()}")  # Should be 145

    print(f"Call Buy Max Profit: {call_buy.calculate_max_profit()}")  # Should be Inf
    print(f"Put Buy Max Profit: {put_buy.calculate_max_profit()}")  # Should be 145
    print(f"Call Sell Max Profit: {call_sell.calculate_max_profit()}")  # Should be 5
    print(f"Put Sell Max Profit: {put_sell.calculate_max_profit()}")  # Should be 5

    print(f"Call Buy Max Loss: {call_buy.calculate_max_loss()}")  # Should be 5
    print(f"Put Buy Max Loss: {put_buy.calculate_max_loss()}")  # Should be 5
    print(f"Call Sell Max Loss: {call_sell.calculate_max_loss()}")  # Should be inf
    print(f"Put Sell Max Loss: {put_sell.calculate_max_loss()}")  # Should be inf

    print(f"Call Buy P/L at 160: {call_buy.calculate_profit_loss(160)}")  # Should be 5
    print(f"Put Buy P/L at 140: {put_buy.calculate_profit_loss(140)}")  # Should be 5

    call_buy.set_stop_loss(152)
    print(f"Call Buy Stop Loss: {call_buy.stop_loss}")  # Should be 152
    print(call_buy.get_trade_info())