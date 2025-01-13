import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import QVBoxLayout
import numpy as np


class Plotter:
    def __init__(self, parent_widget):
        """
         Initializes the plotter class with the parent_widget to use for plotting

        Args:
             parent_widget (QWidget): The Qt widget to plot in
        """
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.axes = self.figure.add_subplot(111)
        self.axes.grid(True)  # Enable grid lines
        self.layout = QVBoxLayout(parent_widget)
        self.layout.addWidget(self.canvas)

    def plot_trades(self, trades, current_stock_price):
        """
          Plots the profit/loss curves for the given trades and updates the chart

          Args:
             trades (list): A list of Trade objects.
             current_stock_price (float): The current stock price
        """
        self.axes.clear()  # Clear previous plot

        if not trades:
            self.axes.set_title("No Trades Added")
            self.canvas.draw()
            return

        min_strike = min([trade.strike for trade in trades])
        max_strike = max([trade.strike for trade in trades])

        # Create a range of stock prices around the min/max strikes to plot for
        x_range = np.linspace(min_strike - (0.05 * min_strike), max_strike + (0.05 * max_strike), 400)

        total_pnl = np.zeros_like(x_range, dtype=float)

        # PLOT individual trades and add up to a total
        for trade in trades:
            y_values = np.array([trade.calculate_profit_loss(x) for x in x_range])  # convert to numpy array
            total_pnl += y_values

            # Plot Individual trade:
            trade_label = f"{trade} BE:{trade.calculate_break_even():.2f}"

            # Get line color based on trade
            if trade.trade_type == 'Buy':
                line_color = 'blue' if trade.option_type == 'Call' else 'green'  # Buy Call is blue, Buy Put is green
            else:  # Sell
                line_color = 'purple' if trade.option_type == 'Call' else 'red'  # Sell call is purple, sell put is red

            self.axes.plot(x_range, y_values, label=trade_label, color=line_color,
                           linewidth=1.5)  # add individual trade plot

            # Plot breakeven point for individual trade:
            be_point = trade.calculate_break_even()
            be_color = 'green' if trade.trade_type == 'Buy' else 'red'
            self.axes.axvline(x=be_point, color=be_color, linestyle='--', linewidth=0.7)  # set to red or green

            # Add a point at breakeven
            self.axes.plot(be_point, trade.calculate_profit_loss(be_point), marker='o', markersize=4, color=be_color)

            if trade.stop_loss:  # If there is a stoploss
                self.axes.axvline(x=trade.stop_loss, color='red', linestyle='--', label=f"SL:{trade.stop_loss:.2f}",
                                  linewidth=0.7)

        # Plot Total P/L
        self.axes.plot(x_range, total_pnl, label="Total P/L", color='black', linewidth=2)

        # Current Stock Price line
        self.axes.axvline(x=current_stock_price, color='blue', linestyle=':',
                          label=f"Current Stock:{current_stock_price:.2f}", linewidth=0.7)

        self.axes.set_xlabel("Stock Price")
        self.axes.set_ylabel("Profit/Loss")
        self.axes.set_title("Profit/Loss Chart")
        self.axes.legend(fontsize='small', loc='upper left')  # Enable legend
        self.axes.grid(True)
        self.canvas.draw()