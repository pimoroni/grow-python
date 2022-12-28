from flask import Flask

from grow.moisture import Moisture

sensors = [ Moisture(1),
            Moisture(2),
            Moisture(3) ]

app = Flask(__name__)

def read_sensor(id):
    return str(sensors[id].moisture)

@app.route("/moisture/<int:sensor_id>")
def get_moisture(sensor_id):
    if sensor_id in range(1,4):
        return read_sensor(sensor_id-1)
    else:
        return "Enter a sensor ID between 1 and 3"

@app.route("/moisture")
def get_moistures():
    data = '[{},{},{}]'.format(read_sensor(0),
                               read_sensor(1),
                               read_sensor(2))
    return data

app.run(host='0.0.0.0',port='5000')