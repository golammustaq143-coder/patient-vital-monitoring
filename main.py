import machine
import time
import ujson
from machine import Pin, ADC, I2C
import ds18x20
import onewire
import ssd1306
import network


# ============================================================
# PATIENT / BED INFORMATION
# ============================================================

BED_NUMBER = "04"


# ============================================================
# WIFI
# ============================================================

sta_if = network.WLAN(network.STA_IF)
sta_if.active(True)
sta_if.connect("Wokwi-GUEST", "")


# ============================================================
# OUTPUT DEVICES
# ============================================================

led_green = Pin(25, Pin.OUT)
led_yellow = Pin(26, Pin.OUT)
led_red = Pin(27, Pin.OUT)

buzzer = Pin(14, Pin.OUT)


# ============================================================
# BUTTONS
# ============================================================

btn_ack = Pin(33, Pin.IN, Pin.PULL_UP)
btn_panic = Pin(32, Pin.IN, Pin.PULL_UP)


# ============================================================
# POTENTIOMETERS
# ============================================================

pot_press = ADC(Pin(34))
pot_press.atten(ADC.ATTN_11DB)

pot_pulse = ADC(Pin(35))
pot_pulse.atten(ADC.ATTN_11DB)


# ============================================================
# DS18B20 TEMPERATURE SENSOR
# ============================================================

ow = onewire.OneWire(Pin(4))
ds = ds18x20.DS18X20(ow)
roms = ds.scan()


# ============================================================
# OLED
# ============================================================

i2c = I2C(
    0,
    scl=Pin(22),
    sda=Pin(21)
)

oled = ssd1306.SSD1306_I2C(128, 64, i2c)


# ============================================================
# GRAPH FUNCTION
# ============================================================

def draw_line(x0, y0, x1, y1):

    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)

    dx = abs(x1 - x0)
    dy = abs(y1 - y0)

    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1

    err = dx - dy

    while True:

        if 0 <= x0 < 128 and 0 <= y0 < 64:
            oled.pixel(x0, y0, 1)

        if x0 == x1 and y0 == y1:
            break

        e2 = 2 * err

        if e2 > -dy:
            err -= dy
            x0 += sx

        if e2 < dx:
            err += dx
            y0 += sy


# ============================================================
# GRAPH HISTORY
# ============================================================

MAX_POINTS = 28

history_temp = [37.0] * MAX_POINTS
history_press = [80.0] * MAX_POINTS
history_bpm = [75] * MAX_POINTS
history_spo2 = [98] * MAX_POINTS


# ============================================================
# SYSTEM VARIABLES
# ============================================================

graph_mode = 0

alarm_acked = False
toggle_state = False

last_beep = time.ticks_ms()
last_alert_time = 0
last_temp_read = 0

panic_triggered = False

btn_last_state = 1
btn_press_time = 0


# ============================================================
# INITIAL TEMPERATURE
# ============================================================

temp_c = 37.0
temp_f = 98.6


# ============================================================
# DS18B20 INITIAL CONVERSION
# ============================================================

if roms:

    try:
        ds.convert_temp()
    except:
        pass


# ============================================================
# OLED STARTUP SCREEN
# ============================================================

oled.fill(0)

oled.text("Smart Hospital", 10, 10)
oled.text("Patient Monitor", 5, 28)
oled.text("BED NO: " + BED_NUMBER, 25, 48)

oled.show()

time.sleep(1.2)


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    # --------------------------------------------------------
    # READ TEMPERATURE
    # --------------------------------------------------------

    if time.ticks_diff(
        time.ticks_ms(),
        last_temp_read
    ) > 1000:

        last_temp_read = time.ticks_ms()

        if roms:

            try:

                temp_c = ds.read_temp(roms[0])

                # Celsius → Fahrenheit
                temp_f = (temp_c * 9 / 5) + 32

                ds.convert_temp()

            except:

                pass


    # --------------------------------------------------------
    # READ BLOOD PRESSURE POTENTIOMETER
    # --------------------------------------------------------

    raw_p = pot_press.read()

    # Systolic BP:
    # 90 → 150 mmHg

    systolic_bp = 90 + (raw_p / 4095.0) * 60


    # Diastolic BP:
    # 60 → 100 mmHg

    diastolic_bp = 60 + (raw_p / 4095.0) * 40


    # Respiratory Rate:
    # 12 → 28 /min

    respiratory_rate = 12 + (raw_p / 4095.0) * 16


    # --------------------------------------------------------
    # READ HEART RATE / SPO2 POTENTIOMETER
    # --------------------------------------------------------

    raw_hr = pot_pulse.read()

    # Normal center position:
    # HR ≈ 75 BPM
    #
    # Full range:
    # approximately 40 → 150 BPM

    bpm = 75 + ((raw_hr - 2048) / 2048.0) * 75

    if bpm < 40:
        bpm = 40

    if bpm > 150:
        bpm = 150

    bpm = int(bpm)


    # --------------------------------------------------------
    # SpO2
    # --------------------------------------------------------

    # Center position ≈ 98%
    # Turning the potentiometer toward extreme values
    # gradually reduces SpO2.

    spo2 = 98 - int(
        abs(raw_hr - 2048) / 2048.0 * 13
    )

    if spo2 < 85:
        spo2 = 85

    if spo2 > 100:
        spo2 = 100


    # --------------------------------------------------------
    # UPDATE GRAPH HISTORY
    # --------------------------------------------------------

    history_temp.pop(0)
    history_temp.append(temp_c)

    history_press.pop(0)

    # OLED BP graph uses systolic value
    history_press.append(systolic_bp)

    history_bpm.pop(0)
    history_bpm.append(bpm)

    history_spo2.pop(0)
    history_spo2.append(spo2)


    # ========================================================
    # ACKNOWLEDGEMENT BUTTON
    # ========================================================

    current_btn = btn_ack.value()

    if btn_last_state == 1 and current_btn == 0:

        btn_press_time = time.ticks_ms()

    elif btn_last_state == 0 and current_btn == 1:

        press_duration = time.ticks_diff(
            time.ticks_ms(),
            btn_press_time
        )

        if press_duration < 600:

            graph_mode = (graph_mode + 1) % 4

        else:

            alarm_acked = True
            panic_triggered = False
            buzzer.value(0)

    btn_last_state = current_btn


    # ========================================================
    # PANIC BUTTON
    # ========================================================

    if btn_panic.value() == 0:

        panic_triggered = True


    # ========================================================
    # LOCAL WOKWI STATUS
    # ========================================================

    is_critical = (

        temp_c > 38.5
        or temp_c < 35.0

        or systolic_bp > 150
        or diastolic_bp > 95

        or systolic_bp < 90
        or diastolic_bp < 60

        or spo2 < 90

        or bpm > 130
        or bpm < 50

        or respiratory_rate > 30

        or respiratory_rate < 10

        or panic_triggered
    )


    is_warning = (

        temp_c > 37.5

        or systolic_bp > 129
        or diastolic_bp > 84

        or spo2 < 95

        or bpm > 100
        or bpm < 60

        or respiratory_rate > 20
        or respiratory_rate < 12
    )


    # ========================================================
    # RESET ACKNOWLEDGEMENT WHEN NORMAL
    # ========================================================

    if not is_critical:

        alarm_acked = False


    # ========================================================
    # LED + BUZZER
    # ========================================================

    if is_critical:

        led_green.value(0)
        led_yellow.value(0)
        led_red.value(1)

        if not alarm_acked:

            if time.ticks_diff(
                time.ticks_ms(),
                last_beep
            ) > 200:

                last_beep = time.ticks_ms()

                toggle_state = not toggle_state

                buzzer.value(
                    1 if toggle_state else 0
                )

        else:

            buzzer.value(0)


    elif is_warning:

        led_green.value(0)
        led_yellow.value(1)
        led_red.value(0)

        buzzer.value(0)


    else:

        led_green.value(1)
        led_yellow.value(0)
        led_red.value(0)

        buzzer.value(0)


    # ========================================================
    # IMPORTANT:
    # SEND SENSOR DATA AS JSON
    # ========================================================

    wokwi_data = {

        "patient_id": "BED-" + BED_NUMBER,

        "temperature_f": round(temp_f, 1),

        "temperature_c": round(temp_c, 2),

        "heart_rate": int(bpm),

        "spo2": int(spo2),

        "systolic_bp": round(systolic_bp, 1),

        "diastolic_bp": round(diastolic_bp, 1),

        "respiratory_rate": round(
            respiratory_rate,
            1
        ),

        "panic": bool(panic_triggered),

        "wokwi_status": (
            "CRITICAL"
            if is_critical
            else (
                "WARNING"
                if is_warning
                else "NORMAL"
            )
        )
    }


    # ========================================================
    # SERIAL OUTPUT
    # ========================================================

    print(
        "WOKWI_DATA:"
        + ujson.dumps(wokwi_data)
    )


    # ========================================================
    # OLED DISPLAY
    # ========================================================

    oled.fill(0)


    if panic_triggered:

        oled.text(
            "!! NURSE CALL !!",
            0,
            0
        )

        oled.text(
            "BED NO : " + BED_NUMBER,
            0,
            18
        )

        oled.text(
            "Panic Button",
            0,
            34
        )

        oled.text(
            "STATUS : CRITICAL",
            0,
            50
        )


    else:

        # ----------------------------------------------------
        # FIRST LINE
        # ----------------------------------------------------

        oled.text(
            "T:{:.1f}F".format(temp_f),
            0,
            0
        )

        oled.text(
            "BP:{:.0f}/{:.0f}".format(
                systolic_bp,
                diastolic_bp
            ),
            58,
            0
        )


        # ----------------------------------------------------
        # SECOND LINE
        # ----------------------------------------------------

        oled.text(
            "HR:{} SpO2:{}".format(
                bpm,
                spo2
            ),
            0,
            11
        )


        # ----------------------------------------------------
        # THIRD LINE
        # ----------------------------------------------------

        oled.text(
            "B:" + BED_NUMBER,
            0,
            22
        )


        if is_critical:

            oled.text(
                "CRIT!",
                32,
                22
            )

        elif is_warning:

            oled.text(
                "WARN",
                32,
                22
            )

        else:

            oled.text(
                "NORM",
                32,
                22
            )


        # ----------------------------------------------------
        # GRAPH SELECTION
        # ----------------------------------------------------

        if graph_mode == 0:

            title = "BP"
            data = history_press
            min_val = 60
            max_val = 160

        elif graph_mode == 1:

            title = "HR"
            data = history_bpm
            min_val = 40
            max_val = 160

        elif graph_mode == 2:

            title = "SpO2"
            data = history_spo2
            min_val = 70
            max_val = 100

        else:

            title = "Temp"
            data = history_temp
            min_val = 30
            max_val = 42


        oled.text(
            "[{}]".format(title),
            88,
            22
        )


        # ----------------------------------------------------
        # GRAPH AXIS
        # ----------------------------------------------------

        draw_line(
            10,
            33,
            10,
            63
        )

        draw_line(
            10,
            63,
            127,
            63
        )


        # ----------------------------------------------------
        # GRAPH DATA
        # ----------------------------------------------------

        for i in range(
            len(data) - 1
        ):

            x1 = 11 + (i * 4)
            x2 = 11 + ((i + 1) * 4)

            val1 = max(
                min(data[i], max_val),
                min_val
            )

            val2 = max(
                min(data[i + 1], max_val),
                min_val
            )

            y1 = 62 - int(
                (
                    (val1 - min_val)
                    /
                    (max_val - min_val)
                ) * 28
            )

            y2 = 62 - int(
                (
                    (val2 - min_val)
                    /
                    (max_val - min_val)
                ) * 28
            )

            draw_line(
                x1,
                y1,
                x2,
                y2
            )


    oled.show()


    # ========================================================
    # LOOP DELAY
    # ========================================================

    time.sleep(0.5)