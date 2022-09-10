from dataclasses import dataclass
from datetime import time, datetime, timedelta, timezone
from math import sqrt
import requests
import json
import pprint
from tzlocal import get_localzone # $ pip install tzlocal

MAX_CHARGE = 45000  # Wh
VOLTAGE = 230 * sqrt(3)  # Volts
MIN_CHARGE_SPEED = 6  # Amps
MAX_CHARGE_SPEED = 16  # Amps
POWER_FACTOR = 0.85
local_tz = get_localzone()


@dataclass
class EnergyPrice:
    from_time: datetime
    price: float


def get_prices(date: datetime):
    url = 'https://graphcdn.frankenergie.nl/'

    today = date.strftime('%Y-%m-%d')
    tomorrow = (date+timedelta(days=2)).strftime('%Y-%m-%d')

    data = {
        "query": 'query MarketPrices {marketPricesElectricity(startDate: "' + today
                 + '", endDate: "' + tomorrow + '") {from marketPrice}}'
    }

    response = requests.post(url, json=data)
    return response


def get_state_of_charge_percent(vehicle_id: str) -> float:
    url = 'https://car.eliens.co/get_vehicleinfo/VXKUKZKXZNW066336'
    response = requests.get(url)

    battery_level = json.loads(response.content)['energy'][0]['level']
    print('Current battery charge: {}%'.format(battery_level))
    return battery_level


def percentage_to_wh(percentage: float) -> float:
    return percentage * MAX_CHARGE


def main(finish_charge_time, vehicle_id):
    prices_response = get_prices(datetime.now())
    prices_parsed = json.loads(prices_response.content)['data']['marketPricesElectricity']

    start_time = datetime.now().astimezone(local_tz)
    end_time = datetime.now().replace(hour=finish_charge_time.hour, minute=finish_charge_time.minute,
                                      second=finish_charge_time.second, microsecond=0).astimezone(local_tz)
    if end_time.time() < start_time.time():
        end_time = end_time + timedelta(days=1)

    prices: [EnergyPrice] = list()

    start_time_offset = start_time - timedelta(hours=1)

    for price in prices_parsed:
        segment_start_time = datetime.strptime(price['from'], '%Y-%m-%dT%H:%M:%S.%fZ')\
            .replace(tzinfo=timezone.utc).astimezone(local_tz)

        if start_time_offset <= segment_start_time < end_time:
            prices.append(EnergyPrice(from_time=segment_start_time, price=price['marketPrice']))

    prices.sort(key=lambda ep: ep.price)

    current_percentage = get_state_of_charge_percent(vehicle_id)
    current_charge = percentage_to_wh(current_percentage)

    charge_amounts = dict()

    wh_required = MAX_CHARGE - current_charge
    ah_required = wh_required / VOLTAGE / POWER_FACTOR

    for price in prices:
        if ah_required == 0:
            charge_amounts[price.from_time.hour] = 0
        elif ah_required < MAX_CHARGE_SPEED:
            if ah_required < MIN_CHARGE_SPEED:
                ah_required = MIN_CHARGE_SPEED
            charge_amounts[price.from_time.hour] = ah_required
            ah_required = 0
        else:
            charge_amounts[price.from_time.hour] = MAX_CHARGE_SPEED
            ah_required -= MAX_CHARGE_SPEED

    current_hour = datetime.now().hour
    return charge_amounts[current_hour]


if __name__ == '__main__':
    pp = pprint.PrettyPrinter(indent=4)
    current_hour_charge_speed = main(finish_charge_time=time.fromisoformat('07:00:00'), vehicle_id='')
    print('Calculated current charging power to {} A'.format(current_hour_charge_speed))
