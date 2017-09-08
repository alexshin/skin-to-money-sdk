# SkinToMoney SDK

Python3 SDK for (https://skintomoney.com/tutorial/api)

## Installation

- Create partner account at https://skintomoney.com
- Get your partner id and secret key
- Grab this SDK and enjoy it

## How it works

SDK contains three classes:

- `STMSignature` - create signature for your request
- `STMApi` - API wrapper
- `STMResponse` - response from API


### Examples how to use it

```python
from api_utils import STMApi

api = STMApi(url='https://skintomoney.com/api/v1', salt='secret', partner_id='partnerid')

# Get for market items for CSGO
market_items_response = api.get_market_list_items(appid=730)  # STMResponse
if not market_items_response.is_error:
    print(market_items_response.error)
else:
    market_items = market_items_response.get()

# Get market history
market_history_response = api.get_market_history()

# Get market history
buy_item_response = api.do_market_buy_item(id='id', price=10.10, currency='RUB', trade_link='url')

# Create order
create_order_response = api.create_order(amount=100, successUrl='url', failUrl='url')

# Get order info
order_info_response = api.get_order_info(idtr='id trans')

# etc
```

### Additional attributes

In some cases your request should contain other attributes. 
For example: `create_order` can contain `sandbox`

In these cases you can add additional arguments into named arguments:
`api.create_order(amount=100, successUrl='url', failUrl='url', sandbox=True)`