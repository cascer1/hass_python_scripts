from dataclasses import dataclass
from datetime import datetime
from itertools import starmap
from math import sqrt

MAX_CHARGE = 50000  # Wh
VOLTAGE = 230 * sqrt(3)  # Volts
MIN_CHARGE_SPEED = 1  # Amps
MAX_CHARGE_SPEED = 16  # Amps


@dataclass
class EnergyPrice:
    from_time: datetime
    to_time: datetime
    price: float


def percentage_to_wh(percentage: float) -> float:
    return percentage / 2


def main(finish_charge_time, vehicle_id):
    prices = [
        EnergyPrice(),
        EnergyPrice(),
        EnergyPrice(),
        EnergyPrice()
    ]

    prices.sort(prices, key=lambda ep: ep.price)

    current_percentage = 0  # TODO: get with the VID
    current_charge = percentage_to_wh(current_percentage)

    charge_amounts = dict()

    wh_required = MAX_CHARGE - current_charge
    ah_required = wh_required / VOLTAGE

    for price in prices:
        if ah_required == 0:
            charge_amounts[price.from_time.hour] = 1
        elif ah_required < 16:
            charge_amounts[price.from_time.hour] = ah_required
            ah_required = 0
        else:
            charge_amounts[price.from_time.hour] = 16
            ah_required -= 16

    current_hour = datetime.now().hour
    return charge_amounts[current_hour]


if __name__ == '__main__':
    main()§