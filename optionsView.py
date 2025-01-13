import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import pandas as pd  # Use 'pd' for pandas
import numpy as np  # Use 'np' for NumPy
import matplotlib.pyplot as plt
from tkinter import Toplevel
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D

# Global Variables
trades = []
calls = None
puts = None
expiration_dates = []


# Fetch the latest stock price
def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        last_price = stock.history(period="1d")["Close"].iloc[-1]
        return last_price
    except Exception as e:
        print(f"Error fetching stock price for {ticker}: {e}")
        return None


# Fetch expiration dates
def fetch_expirations():
    ticker = stock_entry.get().strip().upper()
    if not ticker:
        messagebox.showerror("Error", "Please enter a stock ticker.")
        return

    try:
        stock = yf.Ticker(ticker)
        global expiration_dates
        expiration_dates = stock.options
        exp_date_dropdown["values"] = expiration_dates
        exp_date_dropdown.current(0)
        stock_price = get_stock_price(ticker)
        if stock_price:
            stock_price_label.config(text=f"Last Price: ${stock_price:.2f}")
        messagebox.showinfo("Success", f"Expiration dates fetched for {ticker}.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch expiration dates: {e}")


# Fetch options chain
def fetch_options():
    global calls, puts
    ticker = stock_entry.get().strip().upper()
    exp_date = exp_date_var.get().strip()

    if not ticker or not exp_date:
        messagebox.showerror("Error", "Please enter both stock ticker and select an expiration date.")
        return

    try:
        stock = yf.Ticker(ticker)
        options_chain = stock.option_chain(exp_date)
        calls = options_chain.calls
        puts = options_chain.puts

        # Display calls
        calls_table.delete(*calls_table.get_children())
        for _, row in calls.iterrows():
            calls_table.insert("", "end", values=(row["strike"], row["bid"], row["ask"], row["lastPrice"]))

        # Display puts
        puts_table.delete(*puts_table.get_children())
        for _, row in puts.iterrows():
            puts_table.insert("", "end", values=(row["strike"], row["bid"], row["ask"], row["lastPrice"]))

        messagebox.showinfo("Success", "Options chain fetched successfully.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to fetch options: {e}")


# Add trade to strategy
def add_trade():
    global trades
    trade_type = trade_type_var.get()
    action = action_var.get()
    strike_price = strike_entry.get()
    price_type = price_type_var.get()

    if not (trade_type and action and strike_price and price_type):
        messagebox.showerror("Error", "Please fill in all fields.")
        return

    try:
        strike_price = float(strike_price)
        option_data = calls if trade_type == "Call" else puts
        selected_option = option_data[option_data["strike"] == strike_price]

        if selected_option.empty:
            messagebox.showerror("Error", f"No {trade_type} found with strike price {strike_price}.")
            return

        # Get price with fallback if selected price is zero
        price = selected_option[price_type].values[0]
        if price == 0:
            price = selected_option["lastPrice"].values[0]  # Fallback to "lastPrice"
            if price == 0:
                messagebox.showerror("Error", "No valid price found for the selected option.")
                return

        trades.append({"type": trade_type.lower(), "action": action.lower(), "strike": strike_price, "price": price})
        print(f"Added trade: {trade_type}, {action}, Strike: {strike_price}, Price: {price}")  # Debug print
        messagebox.showinfo("Success", f"Trade added: {action} {trade_type} at {strike_price} for {price}.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to add trade: {e}")


from matplotlib.lines import Line2D


def plot_pl():
    if not trades:
        messagebox.showerror("Error", "No trades to plot.")
        return

    # Determine stock price range around the strike price
    all_strikes = [trade["strike"] for trade in trades]
    min_strike = min(all_strikes)
    max_strike = max(all_strikes)
    price_padding = 20  # Amount to extend around the strike price
    stock_prices = np.linspace(min_strike - price_padding, max_strike + price_padding, 500)

    total_pl = np.zeros(len(stock_prices))
    call_pl = np.zeros(len(stock_prices))
    put_pl = np.zeros(len(stock_prices))
    net_credit = 0  # Track the net credit or debit

    trade_info = "Trades:\n"
    call_break_even = None
    put_break_even = None
    put_stop_price = None  # Track the put stop price

    for trade in trades:
        trade_info += f"{trade['type'].capitalize()}, {trade['action'].capitalize()}, Strike: {trade['strike']}, Price: {trade['price']}\n"

        # Handle calls
        if trade["type"] == "call":
            if trade["action"] == "buy":
                pl = np.maximum(stock_prices - trade["strike"], 0) - trade["price"]
                net_credit -= trade["price"]
                if call_break_even is None:
                    call_break_even = trade["strike"] + trade["price"]
            else:  # Sell
                pl = trade["price"] - np.maximum(stock_prices - trade["strike"], 0)
                net_credit += trade["price"]
                if call_break_even is None:
                    call_break_even = trade["strike"] - trade["price"]

            call_pl += pl

        # Handle puts
        if trade["type"] == "put":
            if trade["action"] == "buy":
                pl = np.maximum(trade["strike"] - stock_prices, 0) - trade["price"]
                net_credit -= trade["price"]
                if put_break_even is None:
                    put_break_even = trade["strike"] - trade["price"]
            else:  # Sell
                pl = trade["price"] - np.maximum(trade["strike"] - stock_prices, 0)
                net_credit += trade["price"]
                if put_break_even is None:
                    put_break_even = trade["strike"] + trade["price"]
                if put_stop_price is None:
                    put_stop_price = trade["strike"] - trade["price"]  # Calculate put stop price

            put_pl += pl

        # Update total P/L for every trade
        total_pl += pl

    # Add break-even points and put stop price to the trade info box
    if call_break_even:
        trade_info += f"Call Break-even: {call_break_even:.2f}\n"
    if put_break_even:
        trade_info += f"Put Break-even: {put_break_even:.2f}\n"
    if put_stop_price:
        trade_info += f"Put Stop Price: {put_stop_price:.2f}\n"
    trade_info += f"Net Credit/Debit: {net_credit:.2f}\n"

    # Create a new Tkinter Toplevel window for the plot
    plot_window = Toplevel(root)
    plot_window.title("Options Strategy P/L")

    # Create a Matplotlib figure
    fig = Figure(figsize=(10, 6), dpi=100)
    ax = fig.add_subplot(111)

    # Helper function to plot dynamically colored lines
    def plot_dynamic_color(x, y, ax, label, positive_color, negative_color):
        for i in range(len(x) - 1):
            color = positive_color if y[i] >= 0 else negative_color
            ax.plot(x[i:i + 2], y[i:i + 2], color=color, linewidth=2, label=label if i == 0 else "")

    # Plot the P/L curves with dynamic colors
    plot_dynamic_color(stock_prices, call_pl, ax, "Call P/L", "blue", "red")
    plot_dynamic_color(stock_prices, put_pl, ax, "Put P/L", "green", "red")
    plot_dynamic_color(stock_prices, total_pl, ax, "Total P/L", "aqua", "red")

    # Add horizontal and vertical gridlines
    ax.axhline(0, color="black", linestyle="--", linewidth=1)
    ax.set_xticks(np.arange(min_strike - price_padding, max_strike + price_padding + 1, 5))  # Customize x-ticks
    ax.grid(True)

    # Set chart titles and labels
    ax.set_title("Options Strategy P/L")
    ax.set_xlabel("Stock Price")
    ax.set_ylabel("Profit/Loss")

    # Create custom legend lines with positive colors
    legend_lines = [
        Line2D([0], [0], color="blue", lw=2, label="Call P/L"),
        Line2D([0], [0], color="green", lw=2, label="Put P/L"),
        Line2D([0], [0], color="aqua", lw=2, label="Total P/L")
    ]
    ax.legend(handles=legend_lines, loc="upper left", bbox_to_anchor=(1, 1))

    # Display trade info as a separate text box in the upper-left corner
    ax.text(
        0.02, 0.98, trade_info,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        horizontalalignment="left",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.8)
    )

    # Embed the plot into the Tkinter window
    canvas = FigureCanvasTkAgg(fig, master=plot_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)


# GUI Setup
root = tk.Tk()
root.title("Options Strategy Builder")

# Input: Stock ticker
tk.Label(root, text="Stock Ticker:").grid(row=0, column=0)
stock_entry = tk.Entry(root)
stock_entry.grid(row=0, column=1)

fetch_exp_btn = tk.Button(root, text="Fetch Expirations", command=fetch_expirations)
fetch_exp_btn.grid(row=1, column=0, columnspan=2)

# Expiration Dropdown
tk.Label(root, text="Expiration Date:").grid(row=2, column=0)
exp_date_var = tk.StringVar()
exp_date_dropdown = ttk.Combobox(root, textvariable=exp_date_var)
exp_date_dropdown.grid(row=2, column=1)

# Stock price display
stock_price_label = tk.Label(root, text="Last Price: Not fetched")
stock_price_label.grid(row=3, column=0, columnspan=2)

# Fetch options button
fetch_btn = tk.Button(root, text="Fetch Options", command=fetch_options)
fetch_btn.grid(row=4, column=0, columnspan=2)

# Options Chain Display
tk.Label(root, text="Calls").grid(row=5, column=0)
calls_table = ttk.Treeview(root, columns=("Strike", "Bid", "Ask", "Last"), show="headings", height=5)
calls_table.heading("Strike", text="Strike")
calls_table.heading("Bid", text="Bid")
calls_table.heading("Ask", text="Ask")
calls_table.heading("Last", text="Last")
calls_table.grid(row=6, column=0)

tk.Label(root, text="Puts").grid(row=5, column=1)
puts_table = ttk.Treeview(root, columns=("Strike", "Bid", "Ask", "Last"), show="headings", height=5)
puts_table.heading("Strike", text="Strike")
puts_table.heading("Bid", text="Bid")
puts_table.heading("Ask", text="Ask")
puts_table.heading("Last", text="Last")
puts_table.grid(row=6, column=1)

# Trade Selection
tk.Label(root, text="Trade Type:").grid(row=7, column=0)
trade_type_var = tk.StringVar()
ttk.Combobox(root, textvariable=trade_type_var, values=["Call", "Put"]).grid(row=7, column=1)

tk.Label(root, text="Action:").grid(row=8, column=0)
action_var = tk.StringVar()
ttk.Combobox(root, textvariable=action_var, values=["Buy", "Sell"]).grid(row=8, column=1)

tk.Label(root, text="Strike Price:").grid(row=9, column=0)
strike_entry = tk.Entry(root)
strike_entry.grid(row=9, column=1)

tk.Label(root, text="Price Type:").grid(row=10, column=0)
price_type_var = tk.StringVar()
ttk.Combobox(root, textvariable=price_type_var, values=["bid", "ask", "lastPrice"]).grid(row=10, column=1)

add_trade_btn = tk.Button(root, text="Add Trade", command=add_trade)
add_trade_btn.grid(row=11, column=0, columnspan=2)

# P/L Plot Button
plot_btn = tk.Button(root, text="Plot P/L", command=plot_pl)
plot_btn.grid(row=12, column=0, columnspan=2)


root.mainloop()
