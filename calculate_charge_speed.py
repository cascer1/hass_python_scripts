import json
from datetime import time, datetime, timedelta, timezone
from math import sqrt

import requests
from tzlocal import get_localzone

MAX_CHARGE = 45000  # Wh
VOLTAGE = 230 * sqrt(3)  # Volts
MIN_CHARGE_SPEED = 6  # Amps
MAX_CHARGE_SPEED = 16  # Amps
POWER_FACTOR = 0.85
local_tz = get_localzone()


class EnergyPrice:
    from_time = datetime.now()
    price = 0.00

    def __init__(self, from_time: datetime, price: float):
        self.from_time = from_time
        self.price = price


def get_prices(date: datetime):
    url = 'https://graphcdn.frankenergie.nl/'

    today = date.strftime('%Y-%m-%d')
    tomorrow = (date + timedelta(days=2)).strftime('%Y-%m-%d')

    data = {
        "query": 'query MarketPrices {marketPricesElectricity(startDate: "' + today
                 + '", endDate: "' + tomorrow + '") {from marketPrice}}'
    }

    response = task.executor(requests.post, url, json=data)
    # response = requests.post(url, json=data)

    return response


def get_state_of_charge_percent(vehicle_id: str) -> float:
    url = 'https://car.eliens.co/get_vehicleinfo/' + vehicle_id

    response = task.executor(requests.get, url)
    # response = requests.get(url)

    battery_level = json.loads(response.content)['energy'][0]['level']
    log.info('Current battery charge: {}%'.format(battery_level))
    # print('Current battery charge: {}%'.format(battery_level))

    return battery_level


def percentage_to_wh(percentage: float) -> float:
    return percentage / 100 * MAX_CHARGE


def main(finish_charge_time, vehicle_id, max_charge_level):
    prices_response = get_prices(datetime.now())
    prices_parsed = json.loads(prices_response.content)['data']['marketPricesElectricity']

    start_time = datetime.now().astimezone(local_tz)
    end_time = datetime.now().replace(hour=finish_charge_time.hour, minute=finish_charge_time.minute,
                                      second=finish_charge_time.second, microsecond=0).astimezone(local_tz)
    if end_time.time() < start_time.time():
        end_time = end_time + timedelta(days=1)

    prices = list()
    start_time_offset = start_time - timedelta(hours=1)

    for price in prices_parsed:
        segment_start_time = datetime.strptime(price['from'], '%Y-%m-%dT%H:%M:%S.%fZ') \
            .replace(tzinfo=timezone.utc).astimezone(local_tz)

        if start_time_offset <= segment_start_time < end_time:
            prices.append(EnergyPrice(from_time=segment_start_time, price=price['marketPrice']))

    prices.sort(key=lambda ep: ep.price)

    current_percentage = get_state_of_charge_percent(vehicle_id)
    current_charge = percentage_to_wh(current_percentage)

    charge_amounts = dict()

    session_max_charge = MAX_CHARGE * (max_charge_level / 100)
    wh_required = session_max_charge - current_charge

    if wh_required < 0:
        wh_required = 0

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
    return int(charge_amounts[current_hour])


@service
def calculate_charge_speed():
    """Calculate the optimal car charging speed based on current battery level and desired full time"""
    vehicle_id = input_text.charge_vehicle_number
    finish_time = input_text.charge_full_time
    max_charge_level = float(input_number.max_car_charge)

    desired_charge_speed = main(finish_charge_time=time.fromisoformat(finish_time),
                                vehicle_id=vehicle_id,
                                max_charge_level=max_charge_level)

    input_number.set_value(entity_id="input_number.charge_speed", value=desired_charge_speed)
