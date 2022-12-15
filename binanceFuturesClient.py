import traceback, pprint

from binance.um_futures import UMFutures
from binance.helpers import round_step_size


class BinanceFutures():
    """
    This is an interface for Binance Futures API for the following basic utils:
    1) Get account's balance (USDT, BUSD)
    2) List available futures
    3) Get necessary trading params:
        min_size, price, price_precision, 
        quantity_precision, step_size, tick_size
    4) Set leverage, margin type, position mode
    5) Place market and limit order
    7) Place stop loss and take profit order based on a given percentage
    8) Close all open positions
    9) Cancel all placed orders

    Useful links:
        https://github.com/binance/binance-futures-connector-python
        https://binance-docs.github.io/apidocs/futures/en/#sdk-and-code-demonstration
        https://testnet.binancefuture.com/en/futures/BTCUSDT
    
    For testnet usage set:
        base_url = "https://testnet.binancefuture.com"
    """

    def __init__(self, apikey, apisecret, base_url= "https://fapi.binance.com", **kwargs):
        self.client = UMFutures(apikey, apisecret, base_url= base_url, **kwargs)
        self.get_precisions()


    def get_balance(self, coin= "USDT"):
        balance = 0
        try:
            response = self.client.balance(recvWindow= 6000)
            for r in response:
                if r['asset'] == coin:
                    balance = float(r['balance']) 
                    break
            
            return(balance)
        except Exception as e:
            print(f"Error: Get futures balance:\n{traceback.format_exc()}")
            return(e)
    

    def get_futures(self, coin= "USDT"):
        try:
            response = self.client.exchange_info()
            all_futures = [r['symbol'] for r in response['symbols'] if r['symbol'][-4:] == coin]
            all_futures.sort()
            return(all_futures)
        except Exception as e:
            print(f"Error: Get futures pairs:\n{traceback.format_exc()}")
            return(e)


    def get_precisions(self):
        try:
            info = self.client.exchange_info()
            self.__quantity_precisions = {}
            self.__prices_precisions = {}
            self.__step_sizes = {}
            self.__tick_sizes = {}
            self.__min_sizes = {}

            for item in info['symbols']: 
                self.__quantity_precisions[item['symbol']] = item['quantityPrecision']
                self.__prices_precisions[item['symbol']] = item['pricePrecision']

                for symbol_filter in item['filters']:
                    if symbol_filter['filterType'] == "PRICE_FILTER":
                        self.__tick_sizes[item['symbol']] = float(symbol_filter['tickSize'])
                    if symbol_filter['filterType'] == "LOT_SIZE":
                        self.__min_sizes[item['symbol']] = float(symbol_filter['minQty'])
                        self.__step_sizes[item['symbol']] = float(symbol_filter['stepSize'])

        except Exception as e:
            print(f"Error: Get futures precisions:\n{traceback.format_exc()}")
    

    def get_pair_parameters(self, pair= "BTCUSDT"):
        try:
            min_size = self.__min_sizes[pair]
            price = float(self.client.ticker_price(pair)['price'])
            price_precision = self.__prices_precisions[pair]
            quantity_precision = self.__quantity_precisions[pair]
            step_size = self.__step_sizes[pair]
            tick_size = self.__tick_sizes[pair] if pair != "BTCUSDT" else 0.1

            params = {
                "min_size": min_size,
                "price": price,
                "price_precision": price_precision,
                "quantity_precision": quantity_precision,
                "step_size": step_size,
                "tick_size": tick_size
            }
            return(params)
        except Exception as e:
            print(f"Error: Get futures price:\n{traceback.format_exc()}")
            return({"error": e})
    

    def set_leverage(self, pair, leverage= 1):
        try:
            leverage_response = self.client.change_leverage(pair, leverage = leverage, recvWindow= 6000)
            print(leverage_response)
        except Exception as e:
            print(f"Error: Set futures leverage:\n{traceback.format_exc()}")
    

    def set_margin_type(self, pair, margin_type= "ISOLATED"):
        """ margin_type = ["CROSSED", "ISOLATED"] """
        try:
            margin_response = self.client.change_margin_type(pair, margin_type, recvWindow= 6000)
            print(margin_response)
        except Exception as e:
            print(f"Error: Set futures margin type:\n{traceback.format_exc()}")


    def change_position_mode(self, mode= "one-way"):
        try:
            is_dual_side = self.client.get_position_mode()['dualSidePosition']

            if is_dual_side and mode == "one-way":
                res = self.client.change_position_mode(dualSidePosition= False, recvWindow= 6000)
            elif not is_dual_side and mode == "hedge":
                res = self.client.change_position_mode(dualSidePosition= True, recvWindow= 6000)
            else:
                res = "No need to change position mode"
            print(res)
        except Exception as e:
            print(f"Error: Change position mode:\n{traceback.format_exc()}")
    
    
    def make_order(self, pair, side, quantity, market, positionSide= "BOTH", timeInForce= None, price= None, stopPrice= None, workingType= "CONTRACT_PRICE", priceProtect= False, closePosition= False):
        orderObj = {
            "symbol": pair,
            "side": side, # BUY for long, SELL for short
            "positionSide": positionSide, # default BOTH for one-way, LONG and SHORT for hedge mode
            "type": market, 
            "quantity": quantity, # Precise quantity
            "timeInForce": timeInForce,
            "price": price,
            "stopPrice": stopPrice,
            "workingType": workingType,
            "priceProtect": priceProtect,
            "closePosition": closePosition,
        }

        try:
            order = self.client.new_order(**orderObj, recvWindow= 6000)
            return(order)
        except Exception as e:
            return({"error": e})
    

    def market_order(self, pair, side, precized_quantity):
        """ This is for one-way mode """
        try:
            if side == "long":
                order = self.make_order(pair, "BUY", precized_quantity, "MARKET")
            else:
                order = self.make_order(pair, "SELL", precized_quantity, "MARKET")
            pprint.pprint(order)
            return(order)
        except Exception as e:
            print(f"Error: Place market order:\n{traceback.format_exc()}")
            return({"error": e})
    

    def limit_order(self, pair, side, precized_quantity, limit_price, tick_size):
        """ This is for one-way mode """
        try:
            limit_price_round = round_step_size(limit_price, tick_size)
            if side == "long":
                order = self.make_order(pair, "BUY", precized_quantity, "LIMIT", "BOTH", "GTC", limit_price_round)
            else:
                order = self.make_order(pair, "SELL", precized_quantity, "LIMIT", "BOTH", "GTC", limit_price_round)
            pprint.pprint(order)
            return(order)
        except Exception as e:
            print(f"Error: Place limit order:\n{traceback.format_exc()}")
            return({"error": e})
    

    def stop_loss_order(self, pair, side, precized_quantity, stoploss, tick_size):
        """ This is for one-way mode.
            Percentage stop loss 
        """
        try:
            price = float(self.client.ticker_price(pair)['price'])
            positions = self.client.account()['positions']

            if side == "long":
                stoploss_price = round_step_size(price * (1 - stoploss / 100), tick_size) 

                for pos in positions:
                    if pos['symbol'] == pair and abs(float(pos['positionAmt'])) > 0:
                        if float(pos['positionAmt']) > 0 and pos['positionSide'] == "LONG":
                            order = self.make_order(pair, "SELL", None, "STOP_MARKET", "BOTH", "GTE_GTC", None, stoploss_price, "MARK_PRICE", True, True) 
                            pprint.pprint(order)
                            return(order)
                
                buy_order = self.market_order(pair, side, precized_quantity)
                order = self.make_order(pair, "SELL", None, "STOP_MARKET", "BOTH", "GTE_GTC", None, stoploss_price, "MARK_PRICE", True, True) 
            else:
                stoploss_price = round_step_size(price * (1 + stoploss / 100), tick_size) 

                for pos in positions:
                    if pos['symbol'] == pair and abs(float(pos['positionAmt'])) > 0:
                        if float(pos['positionAmt']) < 0 and pos['positionSide'] == "SHORT":
                            order = self.make_order(pair, "BUY", None, "STOP_MARKET", "BOTH", "GTE_GTC", None, stoploss_price, "MARK_PRICE", True, True) 
                            pprint.pprint(order)
                            return(order)

                sell_order = self.market_order(pair, side, precized_quantity)
                order = self.make_order(pair, "BUY", None, "STOP_MARKET", "BOTH", "GTE_GTC", None, stoploss_price, "MARK_PRICE", True, True) 
            
            pprint.pprint(order)
            return(order)
        except Exception as e:
            print(f"Error: Place stop loss order:\n{traceback.format_exc()}")
            return({"error": e})


    def take_profit_order(self, pair, side, precized_quantity, takeprofit, tick_size):
        """ This is for one-way mode.
            Percentage take profit
        """
        try:
            price = float(self.client.ticker_price(pair)['price'])
            positions = self.client.account()['positions']

            if side == "long":
                takeprofit_price = round_step_size(price * (1 + takeprofit / 100), tick_size) 

                for pos in positions:
                    if pos['symbol'] == pair and abs(float(pos['positionAmt'])) > 0:
                        if float(pos['positionAmt']) > 0 and pos['positionSide'] == "LONG":
                            order = self.make_order(pair, "SELL", None, "TAKE_PROFIT_MARKET", "BOTH", "GTE_GTC", None, takeprofit_price, "MARK_PRICE", True, True) 
                            pprint.pprint(order)
                            return(order)

                buy_order = self.market_order(pair, side, precized_quantity)
                order = self.make_order(pair, "SELL", None, "TAKE_PROFIT_MARKET", "BOTH", "GTE_GTC", None, takeprofit_price, "MARK_PRICE", True, True) 
            else:
                takeprofit_price = round_step_size(price * (1 - takeprofit / 100), tick_size) 

                for pos in positions:
                    if pos['symbol'] == pair and abs(float(pos['positionAmt'])) > 0:
                        if float(pos['positionAmt']) < 0 and pos['positionSide'] == "SHORT":
                            order = self.make_order(pair, "BUY", None, "TAKE_PROFIT_MARKET", "BOTH", "GTE_GTC", None, takeprofit_price, "MARK_PRICE", True, True) 
                            pprint.pprint(order)
                            return(order)

                sell_order = self.market_order(pair, side, precized_quantity)
                order = self.make_order(pair, "BUY", None, "TAKE_PROFIT_MARKET", "BOTH", "GTE_GTC", None, takeprofit_price, "MARK_PRICE", True, True) 

            pprint.pprint(order)
            return(order)
        except Exception as e:
            print(f"Error: Place take profit order:\n{traceback.format_exc()}")
            return({"error": e})
        

    def close_all_positions(self):
        try:
            positions = self.client.account()['positions']
            for pos in positions:
                if abs(float(pos['positionAmt'])) > 0:
                    if float(pos['positionAmt']) > 0:
                        order = self.market_order(pos['symbol'], "short", float(pos['positionAmt']))
                    elif float(pos['positionAmt']) < 0:
                        order = self.market_order(pos['symbol'], "long", -float(pos['positionAmt']))
                    pprint.pprint(order)
            
            message = "close-done"
            print(message)
            return(message)
        except Exception as e:
            print(f"Error: Close all positions:\n{traceback.format_exc()}")
            return({"error": e})
        

    def cancel_all_orders(self):
        try:
            orders = self.client.get_orders()
            order_symbols = [order['symbol'] for order in orders]

            for symbol in order_symbols:
                response = self.client.cancel_open_orders(symbol= symbol, recvWindow= 6000)
                    
            message = "cancel-done"
            print(message)
            return(message)
        except Exception as e:
            print(f"Error: Cancel all orders:\n{traceback.format_exc()}")
            return({"error": e})
