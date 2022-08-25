from datetime import datetime, time, timedelta, timezone

DATE_TIME_STRING_FORMAT = '%Y-%m-%dT%H:%M:%S'
TARIFF_DATE_TIME_STRING_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'

vehicle_id = "abcd"
target_time = time.fromisoformat("07:00:00")
from_date_time = datetime.now().replace(minute=0, second=0, microsecond=0)
from_time = from_date_time.time()
to_date_time = datetime.now().replace(hour=target_time.hour, minute=target_time.minute, second=target_time.second, microsecond=0)

if target_time < from_time:
    print("tomorrow")
    to_date_time += timedelta(days=1)

date_times = [from_date_time]
date_time = from_date_time

while date_time < to_date_time:
    date_time += timedelta(hours=1)
    date_times.append(date_time) # strftime(DATE_TIME_STRING_FORMAT)

print(to_date_time)
print(date_times)

tariff_time = datetime.strptime("2022-08-20T12:00:00.000Z", TARIFF_DATE_TIME_STRING_FORMAT)
now_time = datetime.strptime("2022-08-20T12:00:00.000Z", TARIFF_DATE_TIME_STRING_FORMAT)
tariff_time = tariff_time.replace(tzinfo=timezone.utc)
now_time = now_time.replace(tzinfo=datetime.now().tzinfo).astimezone(timezone.utc)


print(tariff_time)
print(now_time)
