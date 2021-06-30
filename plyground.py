#!/usr/bin/python3

import ntplib

# # using global pool to get the closest server(not many in israel to sync time)
# response = client.request('pool.ntp.org', version=3)
fmt = '%Y-%m-%d %H:%M:%S %Z%z'
# print(response.tx_time)

from datetime import datetime

client = ntplib.NTPClient()
response = client.request('pool.ntp.org', version=3)
print(f"ntp server: pool.ntp.org")
test = int(datetime.fromtimestamp(response.tx_time).strftime('%d'))
print(f"server responded with: {datetime.fromtimestamp(response.tx_time).strftime('%d')}")
print(type(test))