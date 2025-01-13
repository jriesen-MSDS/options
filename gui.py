import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QLineEdit, QPushButton,
                             QComboBox, QTableWidget, QTableWidgetItem,
                             QMessageBox, QAbstractItemView, QScrollArea, QGroupBox,
                             QFormLayout, QListWidget, QTabWidget, QFrame, QSplitter,
                             QDialog, QDialogButtonBox)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal
from data_fetcher import get_filtered_options_data, fetch_options_data
from trade import Trade
import plotter


class OptionsTradingApp(QMainWindow):
    """
     Main application class for Options Trading application
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Options Trading Visualization Tool")
        self.setGeometry(100, 100, 1200, 800)

        self.trades = []  # List to hold added trades
        self.current_stock_price = None
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout(self.central_widget)

        # LEFT: Data Input, Options Data (moved), and Trades List
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        self.main_layout.addWidget(self.left_panel, 2)  # Give this more proportion of space

        self.create_data_input_section()  # create all data input widgets
        self.create_options_table_section()  # Options data tables
        self.create_trades_section()  # create list of trades section

        # RIGHT: Chart
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.main_layout.addWidget(self.right_panel, 3)  # give chart bigger proportion

        self.create_plot_section()  # Charting area

        self.plotter = plotter.Plotter(self.chart_area)  # create plotter instance

        # Set styles to avoid background and box issues
        self.setStyleSheet("background-color: rgb(240, 240, 240);")  # Set overall application background
        self.central_widget.setStyleSheet("background-color: rgb(240, 240, 240);")
        self.left_panel.setStyleSheet("background-color: rgb(240, 240, 240);")
        self.right_panel.setStyleSheet("background-color: rgb(240, 240, 240);")

        self.current_expiration = None  # Store the currently selected expiration date

    def create_data_input_section(self):
        """
         Creates the section for data input
         (ticker, expiration selection etc)
        """
        data_group = QGroupBox("Stock Data Input")
        data_form = QFormLayout()

        # TICKER
        self.ticker_label = QLabel("Enter Ticker Symbol:")
        self.ticker_input = QLineEdit()
        self.ticker_input.setPlaceholderText("e.g., AAPL")
        data_form.addRow(self.ticker_label, self.ticker_input)

        # EXPIRATIONS:
        self.expiration_label = QLabel("Select Expiration:")
        self.expiration_dropdown = QComboBox()
        self.expiration_dropdown.addItem("Nearest Expiration Date")  # Placeholder item
        self.expiration_dropdown.setEnabled(False)  # Disable until ticker is entered
        self.expiration_dropdown.currentIndexChanged.connect(
            self.expiration_changed)  # add handler for when the selected expiration changes
        data_form.addRow(self.expiration_label, self.expiration_dropdown)

        # FETCH DATA BUTTON:
        self.fetch_button = QPushButton("Fetch Data")
        self.fetch_button.clicked.connect(self.fetch_data)
        data_form.addRow(self.fetch_button)

        # STOCK PRICE:
        self.stock_price_label = QLabel("Current Stock Price:")
        self.stock_price_display = QLabel("-")
        self.stock_price_display.setFont(QFont("Arial", 12, QFont.Bold))
        data_form.addRow(self.stock_price_label, self.stock_price_display)

        data_group.setLayout(data_form)
        self.left_layout.addWidget(data_group)

    def create_trades_section(self):
        """
         Creates the section for listing user trades
         and displaying profit/loss data
        """
        trades_group = QGroupBox("Current Trades")
        trades_layout = QVBoxLayout()

        # TRADES LIST WIDGET
        self.trades_list = QListWidget()
        trades_layout.addWidget(self.trades_list)
        self.trades_list.setSelectionMode(QAbstractItemView.SingleSelection)  # only allow one item to be selected

        # PL DISPLAY
        self.total_pl_label = QLabel("Total P/L: ")
        self.total_pl_value = QLabel("0.00")
        self.total_pl_value.setFont(QFont("Arial", 12, QFont.Bold))
        trades_layout.addWidget(self.total_pl_label)
        trades_layout.addWidget(self.total_pl_value)

        # TRADE REMOVE
        self.remove_trade_button = QPushButton("Remove Selected Trade")
        self.remove_trade_button.clicked.connect(self.remove_selected_trade)
        trades_layout.addWidget(self.remove_trade_button)

        # SET STOP LOSS BUTTON:
        self.set_stop_loss_button = QPushButton("Set Stop Loss")
        self.set_stop_loss_button.clicked.connect(self.set_stop_loss_for_selected_trade)
        trades_layout.addWidget(self.set_stop_loss_button)

        trades_group.setLayout(trades_layout)
        self.left_layout.addWidget(trades_group)

    def create_options_table_section(self):
        """
         Creates the section for displaying options data
         (calls and puts tables in tabs)
        """
        table_group = QGroupBox("Options Data")
        table_layout = QVBoxLayout()

        # TABS for Call/Puts
        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.table_focus_changed)  # Add tab change event to reset row focus

        # CALLS TABLE
        self.calls_table = QTableWidget()
        self.setup_table(self.calls_table)
        self.calls_table.itemSelectionChanged.connect(lambda: self.handle_table_selection(self.calls_table))
        self.call_tab = QWidget()
        call_layout = QVBoxLayout()
        call_layout.addWidget(self.calls_table)
        self.call_tab.setLayout(call_layout)
        self.tab_widget.addTab(self.call_tab, "Calls")

        # PUTS TABLE
        self.puts_table = QTableWidget()
        self.setup_table(self.puts_table)
        self.puts_table.itemSelectionChanged.connect(lambda: self.handle_table_selection(self.puts_table))
        self.put_tab = QWidget()
        put_layout = QVBoxLayout()
        put_layout.addWidget(self.puts_table)
        self.put_tab.setLayout(put_layout)
        self.tab_widget.addTab(self.put_tab, "Puts")

        table_layout.addWidget(self.tab_widget)

        table_group.setLayout(table_layout)
        self.left_layout.addWidget(table_group)

    def create_plot_section(self):
        """
         Creates the section to display the plotting area
        """
        chart_group = QGroupBox("Profit/Loss Chart")
        chart_layout = QVBoxLayout()
        self.chart_area = QWidget()
        chart_layout.addWidget(self.chart_area)

        chart_group.setLayout(chart_layout)
        self.right_layout.addWidget(chart_group)

    def setup_table(self, table):
        """
        Initializes table with required column headers

        Args:
          table (QTableWidget): The table to be setup.
        """
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels(["Type", "Strike", "Bid", "Ask", "Last Price"])
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QAbstractItemView.SingleSelection)

    def fetch_data(self):
        """
          Fetches options data based on the ticker and updates the GUI
        """
        ticker = self.ticker_input.text().strip().upper()
        if not ticker:
            QMessageBox.warning(self, "Input Error", "Please enter a ticker symbol.")
            return

        self.expiration_dropdown.clear()  # Clear previous expirations

        all_data = fetch_options_data(ticker)  # Get all data including expiration
        if not all_data:
            QMessageBox.critical(self, "Fetch Error", "Could not fetch options data. Ensure ticker is valid.")
            return

        self.current_stock_price = all_data.get('stock_price', None)  # get the stock price from the data
        self.stock_price_display.setText(
            str(self.current_stock_price) if self.current_stock_price else "-")  # Display current stock price

        self.expiration_dropdown.setEnabled(True)  # Enable dropdown now that we have expirations
        expirations = all_data["expirations"]
        for exp in expirations:
            self.expiration_dropdown.addItem(exp)

        if self.current_expiration and self.current_expiration in expirations:
            self.expiration_dropdown.setCurrentText(
                self.current_expiration)  # set to the previously selected expiration if its still there
        else:
            self.expiration_dropdown.setCurrentIndex(0)  # if not set to the first available date
            self.current_expiration = self.expiration_dropdown.currentText()

        self.update_options_tables()  # Update the options table based on currently selected data.
        self.update_chart()  # Update the chart with the new data

    def expiration_changed(self, index):
        """
         Handles logic when the selected expiration date is changed.
         Updates options tables
        """
        self.current_expiration = self.expiration_dropdown.currentText()
        self.update_options_tables()

    def update_options_tables(self):
        """
        Updates the options tables based on the currently selected expiration.
        """
        if not self.ticker_input.text():
            return  # Do not do this operation if there is no ticker

        ticker = self.ticker_input.text().strip().upper()

        filtered_data = get_filtered_options_data(ticker)
        if not filtered_data:
            print("Could not update options table with a valid date")
            return

        calls_data = filtered_data.get("calls", [])
        puts_data = filtered_data.get("puts", [])

        self.populate_table(self.calls_table, calls_data, "Call")
        self.populate_table(self.puts_table, puts_data, "Put")

    def populate_table(self, table, data, option_type):
        """
         Populates the given table with option data

         Args:
              table (QTableWidget): The table to populate (either calls or puts).
              data (list):  List of option data
              option_type (str): The option type ('Call' or 'Put').
        """
        table.clearContents()
        table.setRowCount(len(data))
        for row, item in enumerate(data):
            table.setItem(row, 0, QTableWidgetItem(option_type))  # Set option type
            table.setItem(row, 1, QTableWidgetItem(str(item["strike"])))
            table.setItem(row, 2, QTableWidgetItem(str(item["bid"])))
            table.setItem(row, 3, QTableWidgetItem(str(item["ask"])))
            table.setItem(row, 4, QTableWidgetItem(str(item["lastPrice"])))

    def handle_table_selection(self, table):
        """
         Handles logic when an option row is selected, to add a trade.
         Args:
              table (QTableWidget): The table that has been selected from.
        """
        selected_rows = table.selectionModel().selectedRows()

        if not selected_rows:
            return  # No selection

        if len(selected_rows) > 1:
            QMessageBox.warning(self, "Selection Error", "Please select only one row at a time.")
            table.clearSelection()
            return

        row = selected_rows[0].row()
        item_type = table.item(row, 0).text()
        item_strike = float(table.item(row, 1).text())
        item_last_price = float(table.item(row, 4).text())

        self.add_trade(item_type, item_strike, item_last_price)
        table.clearSelection()  # Clear selection immediately after adding to avoid double clicks

    def add_trade(self, option_type, strike, price):
        """
         Adds trade to the current list of trades and updates GUI accordingly
         Args:
              option_type (str):  'Call' or 'Put'
              strike (float): Strike price of the option
              price (float): Last price of the trade
        """
        trade_type, ok = self.show_trade_type_dialog()  # Get trade type from user
        if not ok:
            return  # If user cancels adding a trade

        new_trade = Trade(trade_type, strike, price, option_type, self.current_stock_price)
        self.trades.append(new_trade)

        self.trades_list.addItem(str(new_trade))  # Add to the trade list
        self.update_chart()
        self.update_pl_display()

    def show_trade_type_dialog(self):
        """
        Displays dialog to select trade type (Buy/Sell)

        Returns:
            tuple: Trade type and bool indicating "ok" or "cancel"
        """
        dialog = QMessageBox()
        dialog.setWindowTitle("Select Trade Type")
        dialog.setText("Choose whether to buy or sell the option")
        buy_button = dialog.addButton("Buy", QMessageBox.AcceptRole)
        sell_button = dialog.addButton("Sell", QMessageBox.AcceptRole)
        cancel_button = dialog.addButton(QMessageBox.Cancel)

        dialog.exec_()

        if dialog.clickedButton() == buy_button:
            return "Buy", True
        if dialog.clickedButton() == sell_button:
            return "Sell", True
        return None, False

    def set_stop_loss_for_selected_trade(self):
        """
         Sets stop loss for selected trade by opening a dialog
        """
        selected_items = self.trades_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Stop Loss", "Please select a trade to set a stop loss for.")
            return

        selected_index = self.trades_list.row(selected_items[0])  # Get index of selected trade from list

        trade_to_edit = self.trades[selected_index]  # grab the trade based on the index

        stop_loss_amount, ok = self.show_stop_loss_dialog()  # open stop loss dialog popup
        if ok:
            trade_to_edit.set_stop_loss(stop_loss_amount)
            self.update_chart()

    def show_stop_loss_dialog(self):
        """
        Opens a dialog to enter stop loss amount
        Returns:
            tuple: stop_loss amount, and bool indicating if "ok" was pressed
        """
        dialog = QDialog(self)
        dialog.setWindowTitle("Enter Stop Loss")

        layout = QVBoxLayout()
        stop_loss_label = QLabel("Stop Loss Price:")
        stop_loss_input = QLineEdit()

        layout.addWidget(stop_loss_label)
        layout.addWidget(stop_loss_input)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)
        dialog.setLayout(layout)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        result = dialog.exec_()
        if result == QDialog.Accepted:
            try:
                stop_loss_amount = float(stop_loss_input.text())
                return stop_loss_amount, True
            except ValueError:
                QMessageBox.warning(self, "Stop Loss Error", "Invalid Stop Loss Amount")
                return None, False
        return None, False

    def remove_selected_trade(self):
        """
          Removes a selected trade from the list
        """
        selected_items = self.trades_list.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "Remove Trade", "Please select a trade to remove.")
            return

        index = self.trades_list.row(selected_items[0])

        del self.trades[index]
        self.trades_list.takeItem(index)  # remove from list widget
        self.update_chart()
        self.update_pl_display()

    def table_focus_changed(self, index):
        """
          Clear table selections when tab selection changes
          Args:
              index (int): The index of the tab being focused.
          """
        if index == 0:  # Calls Tab
            if hasattr(self, 'puts_table'):  # Make sure the attribute exists
                self.puts_table.clearSelection()
        elif index == 1:  # Puts Tab
            if hasattr(self, 'calls_table'):
                self.calls_table.clearSelection()  # Clear the calls table when Puts tab is selected

    def update_pl_display(self):
        """
         Updates the display showing Total Profit/Loss
        """
        total_pl = 0
        for trade in self.trades:
            total_pl += trade.calculate_profit_loss(self.current_stock_price)

        self.total_pl_value.setText(f"{total_pl:.2f}")

    def update_chart(self):
        """
          Updates the chart to reflect all current trades
        """
        if self.current_stock_price is not None:
            self.plotter.plot_trades(self.trades, self.current_stock_price)
        else:
            print("Error, current stock price not valid, unable to plot")