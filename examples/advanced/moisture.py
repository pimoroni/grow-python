import time

from grow.moisture import Moisture


print("""moisture.py - Print out sensor reading in Hz

Press Ctrl+C to exit!

""")


m1 = Moisture(1)
m2 = Moisture(2)
m3 = Moisture(3)

while True:
    print(f"""1: {m1.moisture}
2: {m2.moisture}
3: {m3.moisture}
""")
    time.sleep(1.0)

