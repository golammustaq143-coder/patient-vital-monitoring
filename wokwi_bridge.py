import serial
import json
import time

SERIAL_PORT = "rfc2217://localhost:4000"
OUTPUT_FILE = "wokwi_data.json"

print("=" * 60)
print("WOKWI → STREAMLIT LIVE DATA BRIDGE")
print("=" * 60)
print()
print("Connecting to Wokwi...")
print("Port:", SERIAL_PORT)
print()

try:
    ser = serial.serial_for_url(
        SERIAL_PORT,
        baudrate=115200,
        timeout=1
    )

    print("✓ Connected to Wokwi!")
    print("✓ Waiting for WOKWI_DATA...")
    print()

except Exception as e:
    print("✗ Could not connect to Wokwi")
    print("Error:", e)
    raise SystemExit


while True:
    try:
        line = ser.readline().decode("utf-8", errors="ignore").strip()

        if not line:
            continue

        if line.startswith("WOKWI_DATA:"):

            json_text = line.replace("WOKWI_DATA:", "", 1)

            try:
                data = json.loads(json_text)

                with open(
                    OUTPUT_FILE,
                    "w",
                    encoding="utf-8"
                ) as f:
                    json.dump(
                        data,
                        f,
                        indent=4
                    )

                print("✓ Live Wokwi data received")
                print(json.dumps(data, indent=4))
                print("-" * 60)

            except json.JSONDecodeError:
                print("✗ Invalid JSON received")

    except KeyboardInterrupt:
        print()
        print("Bridge stopped.")
        break

    except Exception as e:
        print("Bridge error:", e)
        time.sleep(1)