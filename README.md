# binanceFuturesClient
This is an interface for Binance Futures API for the following utilities:

1. Get account's balance (USDT, BUSD)
2. List available futures
3. Get necessary trading params:  
    min_size, price, price_precision,  
    quantity_precision, step_size, tick_size  
4. Set leverage, margin type, position mode
5. Place market and limit order
6. Place stop loss and take profit order based on a given percentage
7. Close all open positions
8. Cancel all placed orders

# Useful links:
1. [binance-futures-connector-python](https://github.com/binance/binance-futures-connector-python)
2. [Binance Futures API](https://binance-docs.github.io/apidocs/futures/en/#sdk-and-code-demonstration)
3. [Binance Futures Testnet](https://testnet.binancefuture.com)

# Installation
Python version >= 3.8.5 is required.  
  
`pip3 install -r requirements.txt`

# Usage:
```python
base_url = "https://testnet.binancefuture.com"

client = BinanceFutures(BINANCE_FUTURES_APIKEY, BINANCE_FUTURES_APISECRET, base_url)

params = client.get_pair_parameters("BTCUSDT")

market_order = client.market_order("BTCUSDT", "long", 0.001)

sl_order = client.stop_loss_order("BTCUSDT", "short", 0.001, 2, params['tick_size'])

client.close_all_positions()
```
