"""
@jorjun Anno Vvii ☉ in ♓ ☽ in ♋
License: MIT
Description: Web API for moisture readings: http://<your-pi-host>:8080/
"""
from functools import partial
import json
import logging
from aiohttp import web
from grow.moisture import Moisture

# Test class
#class Moisture():
  #def __init__(self, channel):
    #self.channel = channel
  #@property
  #def moisture(self):
    #return self.channel *3

json_response = partial(web.json_response, dumps=partial(json.dumps, default=str))
routes = web.RouteTableDef()
@routes.get("/")  # Or whatever URL path you want
async def reading(request):
  data = {
    "m1": meter[0].moisture,
    "m2": meter[1].moisture,
    "m3": meter[2].moisture,
  }
  return json_response(data)

if __name__ == "__main__":
  app = web.Application()
  logging.basicConfig(level=logging.INFO)
  app.add_routes(routes)
  meter = [Moisture(_+1) for _ in range(3)]
  web.run_app(
      app,
        host="0.0.0.0",
        port=8080,
        access_log_format='%s %r [%b / %Tf] "%{User-Agent}i"',
    )