from datetime import timedelta, datetime
import requests
from tzlocal import get_localzone # $ pip install tzlocal
local_tz = get_localzone()

def get_prices(date: datetime):

    url = 'https://graphcdn.frankenergie.nl/'

    today = date.strftime('%Y-%m-%d')
    tomorrow = (date+timedelta(days=1)).strftime('%Y-%m-%d')

    data = {
        "query": 'query MarketPrices {marketPricesElectricity(startDate: "' + today + '", endDate: "'+ tomorrow + '") {till from marketPrice}}'
    }

    response = requests.post(url, json=data)
    return response


if __name__ == "__main__":
    import json
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    response = get_prices(datetime.now())
    parsed = json.loads(response.content)['data']['marketPricesElectricity']
    pp.pprint(parsed)