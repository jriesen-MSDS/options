
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton,
    QLabel, QLineEdit, QComboBox, QListWidget, QTableWidget, QTableWidgetItem, QGridLayout
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np
import yfinance as yf

class OptionsPlotApp(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Options Strategy P/L")
        self.setGeometry(100, 100, 1400, 900)

        # Main widget
        self.main_widget = QWidget(self)
        self.setCentralWidget(self.main_widget)

        # Layouts
        self.layout = QVBoxLayout(self.main_widget)
        self.input_layout = QHBoxLayout()
        self.layout.addLayout(self.input_layout)

        # Ticker and expiration inputs
        self.ticker_label = QLabel("Ticker:")
        self.ticker_input = QLineEdit()
        self.ticker_input.setMaximumWidth(100)
        self.input_layout.addWidget(self.ticker_label)
        self.input_layout.addWidget(self.ticker_input)

        self.stock_price_label = QLabel("Stock Price: N/A")
        self.input_layout.addWidget(self.stock_price_label)

        self.expiration_label = QLabel("Expiration:")
        self.expiration_combo = QComboBox()
        self.expiration_combo.setMaximumWidth(150)
        self.expiration_combo.currentIndexChanged.connect(self.update_option_chain)
        self.input_layout.addWidget(self.expiration_label)
        self.input_layout.addWidget(self.expiration_combo)

        # Fetch data button
        self.fetch_button = QPushButton("Fetch Options")
        self.fetch_button.clicked.connect(self.fetch_options)
        self.input_layout.addWidget(self.fetch_button)

        # Option chain display
        self.option_chain_layout = QGridLayout()
        self.layout.addLayout(self.option_chain_layout)

        self.calls_table = QTableWidget()
        self.calls_table.setColumnCount(5)
        self.calls_table.setHorizontalHeaderLabels(["Type", "Strike", "Bid", "Ask", "Last"])
        self.option_chain_layout.addWidget(QLabel("Calls"), 0, 0)
        self.option_chain_layout.addWidget(self.calls_table, 1, 0)

        self.puts_table = QTableWidget()
        self.puts_table.setColumnCount(5)
        self.puts_table.setHorizontalHeaderLabels(["Type", "Strike", "Bid", "Ask", "Last"])
        self.option_chain_layout.addWidget(QLabel("Puts"), 0, 1)
        self.option_chain_layout.addWidget(self.puts_table, 1, 1)

        # Add trade and clear trades buttons
        self.trade_controls_layout = QHBoxLayout()
        self.layout.addLayout(self.trade_controls_layout)

        self.action_combo = QComboBox()
        self.action_combo.addItems(["Buy", "Sell"])
        self.trade_controls_layout.addWidget(QLabel("Action:"))
        self.trade_controls_layout.addWidget(self.action_combo)

        self.add_trade_button = QPushButton("Add Selected Trade")
        self.add_trade_button.clicked.connect(self.add_trade)
        self.trade_controls_layout.addWidget(self.add_trade_button)

        self.clear_trades_button = QPushButton("Clear Trades")
        self.clear_trades_button.clicked.connect(self.clear_trades)
        self.trade_controls_layout.addWidget(self.clear_trades_button)

        # List of trades
        self.trades_list = QListWidget()
        self.layout.addWidget(self.trades_list)

        # Matplotlib figure and canvas
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.layout.addWidget(self.canvas)

        # Plot button
        self.plot_button = QPushButton("Plot Options P/L")
        self.plot_button.clicked.connect(self.plot_pl)
        self.layout.addWidget(self.plot_button)

        # Trades storage
        self.trades = []
        self.stock_data = None

    def fetch_options(self):
        ticker = self.ticker_input.text()
        if not ticker:
            self.trades_list.addItem("Error: Please enter a valid ticker.")
            return

        try:
            # Fetch stock data and expirations
            stock = yf.Ticker(ticker)
            self.stock_data = stock
            stock_price = stock.info['currentPrice']
            self.stock_price_label.setText(f"Stock Price: {stock_price:.2f}")
            expirations = stock.options
            self.expiration_combo.clear()
            self.expiration_combo.addItems(expirations)

            # Fetch options for the first expiration date
            if expirations:
                self.fetch_option_chain(expirations[0], stock_price)
        except Exception as e:
            self.trades_list.addItem(f"Error: Failed to fetch data for {ticker}. {str(e)}")

    def update_option_chain(self):
        # Update option chain based on selected expiration date
        if not self.stock_data:
            return
        selected_expiration = self.expiration_combo.currentText()
        stock_price = float(self.stock_price_label.text().split(":")[1].strip())
        self.fetch_option_chain(selected_expiration, stock_price)

    def fetch_option_chain(self, expiration, stock_price):
        try:
            if not self.stock_data:
                return
            options = self.stock_data.option_chain(expiration)
            calls = options.calls
            puts = options.puts

            # Limit strikes to 10 above and 10 below the stock price
            min_strike = stock_price - 10 * 5  # Assume 5-point intervals
            max_strike = stock_price + 10 * 5
            calls = calls[(calls['strike'] >= min_strike) & (calls['strike'] <= max_strike)]
            puts = puts[(puts['strike'] >= min_strike) & (puts['strike'] <= max_strike)]

            # Populate the calls table
            self.calls_table.setRowCount(len(calls))
            for i, row in enumerate(calls.itertuples()):
                self.calls_table.setItem(i, 0, QTableWidgetItem("call"))
                self.calls_table.setItem(i, 1, QTableWidgetItem(f"{row.strike:.2f}"))
                self.calls_table.setItem(i, 2, QTableWidgetItem(f"{row.bid:.2f}"))
                self.calls_table.setItem(i, 3, QTableWidgetItem(f"{row.ask:.2f}"))
                self.calls_table.setItem(i, 4, QTableWidgetItem(f"{row.lastPrice:.2f}"))

            # Populate the puts table
            self.puts_table.setRowCount(len(puts))
            for i, row in enumerate(puts.itertuples()):
                self.puts_table.setItem(i, 0, QTableWidgetItem("put"))
                self.puts_table.setItem(i, 1, QTableWidgetItem(f"{row.strike:.2f}"))
                self.puts_table.setItem(i, 2, QTableWidgetItem(f"{row.bid:.2f}"))
                self.puts_table.setItem(i, 3, QTableWidgetItem(f"{row.ask:.2f}"))
                self.puts_table.setItem(i, 4, QTableWidgetItem(f"{row.lastPrice:.2f}"))
        except Exception as e:
            self.trades_list.addItem(f"Error: Failed to fetch option chain. {str(e)}")

    def add_trade(self):
        # Determine which table has a selected row
        selected_table = None
        trade_type = None

        # Check if a row is selected in the calls table
        if self.calls_table.selectionModel().hasSelection():
            selected_table = self.calls_table
            trade_type = "call"
            print("Calls table is active.")

        # Check if a row is selected in the puts table
        elif self.puts_table.selectionModel().hasSelection():
            selected_table = self.puts_table
            trade_type = "put"
            print("Puts table is active.")

        # If no table has a selected row
        if not selected_table:
            self.trades_list.addItem("Error: No option selected. Please select a row in one of the tables.")
            print("Error: No table has a selected row.")
            return

        # Get the selected row
        selected_row = selected_table.selectionModel().currentIndex().row()
        if selected_row < 0:
            self.trades_list.addItem("Error: No option selected. No row is selected.")
            print("Error: No row is selected in the active table.")
            return

        try:
            # Gather trade details
            strike = float(selected_table.item(selected_row, 1).text())
            ask_price = float(selected_table.item(selected_row, 3).text())  # Use the Ask price for the trade
            action = self.action_combo.currentText().lower()  # "buy" or "sell"
            print(f"Selected Row {selected_row}: Strike={strike}, Price={ask_price}, Action={action}")

            # Create a trade dictionary
            trade = {
                "type": trade_type,
                "strike": strike,
                "price": ask_price,
                "action": action,
            }

            # Add the trade to the trades list and display it
            self.trades.append(trade)
            self.trades_list.addItem(
                f"Trade {len(self.trades)} ({trade['type'].capitalize()}), {trade['action'].capitalize()}, "
                f"Strike: {trade['strike']}, Price: {trade['price']:.2f}"
            )
            print(f"Trade added: {trade}")
        except Exception as e:
            self.trades_list.addItem(f"Error: Invalid data in the selected option. {str(e)}")
            print(f"Error adding trade: {e}")

        stop_loss_price = None

        if trade["type"] == "call":
            if trade["action"] == "buy":
                stop_loss_price = trade["strike"] + trade["price"]
            elif trade["action"] == "sell":
                stop_loss_price = trade["strike"] - trade["price"]

        elif trade["type"] == "put":
            if trade["action"] == "buy":
                stop_loss_price = trade["strike"] - trade["price"]
            elif trade["action"] == "sell":
                stop_loss_price = trade["strike"] + trade["price"]

        if stop_loss_price is not None:
            self.trades_list.addItem(
                f"{trade['type'].capitalize()}, {trade['action'].capitalize()}, Strike: {trade['strike']}, "
                f"Price: {trade['price']}, Stop-loss: {stop_loss_price:.2f}"
            )

    def clear_trades(self):
        self.trades.clear()
        self.trades_list.clear()

    def plot_pl(self):
        if not self.trades:
            self.trades_list.addItem("Error: No trades to plot!")
            return

        # Clear the previous plot
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        # Determine stock price range
        all_strikes = [trade["strike"] for trade in self.trades]
        min_strike = min(all_strikes)
        max_strike = max(all_strikes)
        price_padding = 20
        stock_prices = np.linspace(min_strike - price_padding, max_strike + price_padding, 500)

        total_pl = np.zeros(len(stock_prices))
        colors = ["blue", "green", "purple", "orange", "red"]  # Colors for individual trades

        for i, trade in enumerate(self.trades):
            # Handle calls
            if trade["type"] == "call":
                if trade["action"] == "buy":
                    pl = np.maximum(stock_prices - trade["strike"], 0) - trade["price"]
                else:  # Sell
                    pl = trade["price"] - np.maximum(stock_prices - trade["strike"], 0)

            # Handle puts
            elif trade["type"] == "put":
                if trade["action"] == "buy":
                    pl = np.maximum(trade["strike"] - stock_prices, 0) - trade["price"]
                else:  # Sell
                    pl = trade["price"] - np.maximum(trade["strike"] - stock_prices, 0)

            total_pl += pl
            ax.plot(stock_prices, pl, label=f"Trade {i + 1} ({trade['type'].capitalize()})", color=colors[i % len(colors)])
        # Add break-even points for each trade
        break_even_points = []
        for i, trade in enumerate(self.trades):
            if trade["type"] == "call":
                if trade["action"] == "buy":
                    break_even = trade["strike"] + trade["price"]
                else:
                    break_even = trade["strike"] - trade["price"]
            elif trade["type"] == "put":
                if trade["action"] == "buy":
                    break_even = trade["strike"] - trade["price"]
                else:
                    break_even = trade["strike"] + trade["price"]

            break_even_points.append(break_even)
            ax.axvline(break_even, color="red", linestyle="--", linewidth=0.8)
            ax.text(
                break_even,
                0,
                f"BE {i + 1}: {break_even:.2f}",
                color="red",
                rotation=90,
                verticalalignment="bottom",
            )
        # Initialize total profit and loss variables
        total_max_profit = 0
        total_max_loss = 0

        for trade in self.trades:
            if trade["type"] == "call":
                if trade["action"] == "buy":
                    max_profit = float('inf')
                    max_loss = trade["price"]
                elif trade["action"] == "sell":
                    max_profit = trade["price"]
                    max_loss = float('-inf')

            elif trade["type"] == "put":
                if trade["action"] == "buy":
                    max_profit = float('inf')
                    max_loss = trade["price"]
                elif trade["action"] == "sell":
                    max_profit = trade["price"]
                    max_loss = float("-inf")

                    total_max_profit += max_profit
                    total_max_loss += max_loss

                    self.trades_list.addItem(f"Total Max Profit: {total_max_profit:.2f}")
                    self.trades_list.addItem(f"Total Max Loss: {total_max_loss:.2f}")

                    # Plot the total P/L curve
        ax.plot(stock_prices, total_pl, label="Total P/L", color="aqua")

        # Add horizontal and vertical gridlines
        ax.axhline(0, color="black", linestyle="--", linewidth=1)
        ax.grid(True)

        # Set chart titles and labels
        ax.set_title("Options Strategy P/L")
        ax.set_xlabel("Stock Price")
        ax.set_ylabel("Profit/Loss")

        # Add a legend
        ax.legend(loc="upper left")

        # Refresh the canvas
        self.canvas.draw()

if __name__ == "__main__":
    app = QApplication([])
    window = OptionsPlotApp()
    window.show()
    app.exec_()
