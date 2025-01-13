import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# Fetch stock and options data
def get_synthetic_long_with_extra_legs(ticker, expiration_date=None):
    # Fetch stock data
    stock = yf.Ticker(ticker)
    stock_data = stock.history(period="1mo")

    if stock_data.empty:
        raise ValueError(f"No stock data available for {ticker}")

    # Fetch available options expiration dates
    available_expirations = stock.options

    if not available_expirations:
        raise ValueError(f"No options data available for {ticker}")

    # Use the nearest expiration if none is provided
    if expiration_date is None:
        expiration_date = available_expirations[0]
    elif expiration_date not in available_expirations:
        raise ValueError(f"Expiration `{expiration_date}` cannot be found. Available expirations are: {available_expirations}")

    # Fetch options chain
    try:
        options_chain = stock.option_chain(expiration_date)
    except Exception as e:
        raise ValueError(f"Failed to fetch options chain for {ticker} on {expiration_date}: {e}")

    # Extract calls and puts
    calls = options_chain.calls
    puts = options_chain.puts

    if calls.empty or puts.empty:
        raise ValueError("Options data is empty.")

    # Get current stock price
    current_price = stock_data['Close'].iloc[-1]

    # Find the closest strike price to the current price
    closest_strike = calls.iloc[(calls['strike'] - current_price).abs().idxmin()]['strike']

    # Filter for the synthetic long strike and extra legs
    synthetic_calls = calls[calls['strike'] == closest_strike]
    synthetic_puts = puts[puts['strike'] == closest_strike]
    extra_call = calls[calls['strike'] > closest_strike].iloc[0] if not calls[calls['strike'] > closest_strike].empty else None
    extra_put = puts[puts['strike'] < closest_strike].iloc[-1] if not puts[puts['strike'] < closest_strike].empty else None

    # Calculate breakeven prices
    call_premium = synthetic_calls['lastPrice'].values[0] if not synthetic_calls.empty else 0
    put_premium = synthetic_puts['lastPrice'].values[0] if not synthetic_puts.empty else 0

    # Prepare synthetic long position with extra legs
    synthetic_long = pd.DataFrame({
        'Strike': [closest_strike],
        'Call Premium': [call_premium],
        'Put Premium': [put_premium],
        'Sell Another Call Strike': [extra_call['strike']] if extra_call is not None else [None],
        'Sell Another Call Premium': [extra_call['lastPrice']] if extra_call is not None else [None],
        'Sell Another Put Strike': [extra_put['strike']] if extra_put is not None else [None],
        'Sell Another Put Premium': [extra_put['lastPrice']] if extra_put is not None else [None],
    })

    return stock_data, synthetic_long, available_expirations

# Visualization function
def visualize_synthetic_long(synthetic_long):
    plt.figure(figsize=(12, 8))

    # Plot Profit/Loss Lines
    strike = synthetic_long['Strike'].iloc[0]
    call_premium = synthetic_long['Call Premium'].iloc[0]
    put_premium = synthetic_long['Put Premium'].iloc[0]
    sell_call_strike = synthetic_long['Sell Another Call Strike'].iloc[0]
    sell_call_premium = synthetic_long['Sell Another Call Premium'].iloc[0]
    sell_put_strike = synthetic_long['Sell Another Put Strike'].iloc[0]
    sell_put_premium = synthetic_long['Sell Another Put Premium'].iloc[0]

    x = range(int(strike - 50), int(strike + 50))

    # Correct synthetic long calculation: buy call + sell put
    synthetic_long_profit = [i - strike - call_premium + (strike - i) + put_premium for i in x]

    # Add impacts of selling another call or put
    synthetic_long_with_sell_call = [pl + (sell_call_premium - max(0, i - sell_call_strike)) for pl, i in zip(synthetic_long_profit, x)]
    synthetic_long_with_sell_put = [pl + (sell_put_premium - max(0, sell_put_strike - i)) for pl, i in zip(synthetic_long_profit, x)]

    # Plot synthetic long and extra legs
    plt.plot(x, synthetic_long_profit, label="Synthetic Long", color="black")
    plt.plot(x, synthetic_long_with_sell_call, label="Synthetic Long + Sell Call", color="orange", linestyle="--")
    plt.plot(x, synthetic_long_with_sell_put, label="Synthetic Long + Sell Put", color="red", linestyle="--")

    # Add Strike Line
    plt.axvline(x=strike, color="purple", linestyle="--", label=f"Strike Price: {strike}")
    plt.axhline(y=0, color="black", linestyle="--")

    plt.title("Profit/Loss for Synthetic Long with Extra Sells")
    plt.xlabel("Stock Price at Expiration")
    plt.ylabel("Profit/Loss ($)")
    plt.legend()
    plt.grid()
    plt.show()

# Example usage
ticker = "AMD"
user_expiration_date = "2025-01-31"  # Example input

try:
    stock_data, synthetic_long, available_expirations = get_synthetic_long_with_extra_legs(ticker, user_expiration_date)

    # Display stock data
    print("Stock Data:")
    print(stock_data.tail())

    # Display synthetic long data with extra legs
    print("\nSynthetic Long Data with Extra Legs:")
    print(synthetic_long)

    # Display available expirations
    print("\nAvailable Expirations:")
    print(available_expirations)

    # Visualize the synthetic long strategy
    visualize_synthetic_long(synthetic_long)

except ValueError as e:
    print(f"Error: {e}")


