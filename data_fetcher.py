import yfinance as yf


def fetch_options_data(ticker):
    """
    Fetches options data for a given ticker.

    Args:
        ticker (str): Stock ticker symbol.

    Returns:
         dict: Dictionary containing calls, puts, expirations, and current stock price.
         None: If the fetch fails.
    """
    try:
        ticker_obj = yf.Ticker(ticker)
        options = ticker_obj.options

        if not options:
            print("No options data found for this ticker.")
            return None

        all_data = {}
        all_data["expirations"] = options
        all_data["calls"] = {}
        all_data["puts"] = {}

        # Fetch data for the first available expiration date
        # (or all if there is only one date)
        for exp_date in options[:1]:  # only use the nearest expiration

            chain = ticker_obj.option_chain(exp_date)
            calls = chain.calls
            puts = chain.puts

            # Filter to get bid, ask, and last price
            if not calls.empty:
                calls_filtered = calls[["strike", "bid", "ask", "lastPrice"]]
                all_data["calls"] = calls_filtered.to_dict(orient='records')
            else:
                all_data["calls"] = []
            if not puts.empty:
                puts_filtered = puts[["strike", "bid", "ask", "lastPrice"]]
                all_data["puts"] = puts_filtered.to_dict(orient='records')
            else:
                all_data["puts"] = []

        all_data["stock_price"] = ticker_obj.info.get("currentPrice", None)
        if all_data["stock_price"] is None:
            all_data["stock_price"] = ticker_obj.info.get("previousClose",
                                                          None)  # Try previous close if current isn't found
        return all_data

    except Exception as e:
        print(f"Error fetching data: {e}")
        return None


def get_filtered_options_data(ticker):
    """
   Fetches options data for a given ticker and filters to get top 10 strikes above and below stock price.

   Args:
       ticker (str): Stock ticker symbol.

   Returns:
       dict: Dictionary containing filtered calls, puts, expirations, and current stock price.
       None: if the fetch or filter fails.
   """
    data = fetch_options_data(ticker)
    if not data or not data["calls"] or not data["puts"] or not data["stock_price"]:
        return None

    stock_price = data["stock_price"]

    calls = data["calls"]
    puts = data["puts"]

    filtered_calls = []
    filtered_puts = []

    # filter calls:
    calls_above = []
    calls_below = []
    for call in calls:
        if call['strike'] >= stock_price:
            calls_above.append(call)
        else:
            calls_below.append(call)

    calls_above.sort(key=lambda x: x["strike"])
    calls_below.sort(key=lambda x: x["strike"], reverse=True)

    filtered_calls = calls_below[:10] + calls_above[:10]

    # filter puts:
    puts_above = []
    puts_below = []
    for put in puts:
        if put['strike'] >= stock_price:
            puts_above.append(put)
        else:
            puts_below.append(put)

    puts_above.sort(key=lambda x: x["strike"])
    puts_below.sort(key=lambda x: x["strike"], reverse=True)

    filtered_puts = puts_below[:10] + puts_above[:10]

    data["calls"] = filtered_calls
    data["puts"] = filtered_puts

    return data


if __name__ == '__main__':
    # Example usage:
    ticker_symbol = 'AAPL'
    filtered_data = get_filtered_options_data(ticker_symbol)

    if filtered_data:
        print(f"Stock Price: {filtered_data['stock_price']}")
        print("Calls:")
        for call in filtered_data['calls']:
            print(call)
        print("\nPuts:")
        for put in filtered_data['puts']:
            print(put)
    else:
        print("Could not fetch options data.")