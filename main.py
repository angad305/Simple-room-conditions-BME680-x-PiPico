# main.py
from epaper_display import EpaperDisplay
from machine import I2C, Pin
import bme680
import time
from bme680IAQ import IAQTracker
import gc

CALIBRATION_CYCLES = 300  # Number of cycles needed for IAQ calibration
CALIBRATION_INTERVAL = 1  # Time between calibration readings (1 second)
NORMAL_READ_INTERVAL = 60  # 120 seconds for normal operation

# Initialize the e-paper display
epaper = EpaperDisplay()

def interpret_air_quality(aq_percent):
    if aq_percent >= 90:
        return "Very Good"
    elif aq_percent >= 70:
        return "Good"
    elif aq_percent >= 50:
        return "Moderate"
    else:
        return "Poor"

def main():
    # Initialize I2C and BME680 sensor
    i2c = I2C(1, scl=Pin(7), sda=Pin(6), freq=100000)

    # Initialize BME680 sensor with the correct address
    sensor = bme680.BME680(i2c_addr=0x77, i2c_device=i2c)

    # Initialize IAQ tracker
    iaq_tracker = IAQTracker()

    # Sensor setup
    sensor.set_humidity_oversample(bme680.OS_2X)
    sensor.set_pressure_oversample(bme680.OS_4X)
    sensor.set_temperature_oversample(bme680.OS_8X)
    sensor.set_filter(bme680.FILTER_SIZE_3)
    sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
    sensor.set_gas_heater_temperature(320)
    sensor.set_gas_heater_duration(150)
    sensor.select_gas_heater_profile(0)

    start_time = time.time()
    remaining_calibration_cycles = CALIBRATION_CYCLES
    last_reading_time = 0

    print("Starting calibration phase...")

    while True:
        try:
            current_time = time.time()

            if sensor.get_sensor_data() and sensor.data.heat_stable:
                temperature = sensor.data.temperature
                pressure = sensor.data.pressure
                humidity = sensor.data.humidity
                gas = sensor.data.gas_resistance

                AQ = iaq_tracker.getIAQ(sensor.data)

                if remaining_calibration_cycles > 0:
                    print(f'Calibrating - Temp: {temperature:.2f} C, Pressure: {pressure:.2f} hPa, Humidity: {humidity:.2f} %RH, Gas: {gas} Ohms, Air Quality: {AQ if AQ is not None else "Calibrating"} (Cycles left: {remaining_calibration_cycles})')
                    remaining_calibration_cycles -= 1
                    time.sleep(CALIBRATION_INTERVAL)
                    if remaining_calibration_cycles == 0:
                        print("Calibration complete. Entering normal operation mode.")
                elif current_time - last_reading_time >= NORMAL_READ_INTERVAL:
                    if AQ is not None:
                        quality = interpret_air_quality(AQ)
                        print(f'Temp: {temperature:.2f} C, Pressure: {pressure:.2f} hPa, Humidity: {humidity:.2f} %RH, Gas: {gas} Ohms, Air Quality: {AQ:.1f}% ({quality})')

                        # Update the display with sensor readings
                        epaper.update_display(temperature,pressure,humidity,quality)

                        last_reading_time = current_time  # Update the last reading time

            else:
                print("Waiting for stable readings...")

        except Exception as e:
            error_message = f"PICO Down - General error for BME680: {str(e)}"
            print(error_message)

        #print("Free memory:", gc.mem_free())
        gc.collect()  # Force garbage collection after each iteration

        # Sleep for a short time to prevent tight looping
        if remaining_calibration_cycles <= 0:
            time.sleep(1)

if __name__ == "__main__":
    main()
