import streamlit as st
import cv2
import time
import mediapipe as mp
import winsound
import math

st.set_page_config(
    page_title="Silent Signal AI",
    layout="wide"
)

# ----------------- HEADER -----------------
st.markdown(
    """
    <h1 style='text-align:center;'>🚨 Silent Signal AI</h1>
    <p style='text-align:center; color:gray;'>
    Real-time gesture-based emergency detection using Computer Vision
    </p>
    """,
    unsafe_allow_html=True
)

# ----------------- LAYOUT -----------------
col_cam, col_info = st.columns([2, 1])

frame_box = col_cam.image([])

status_box = col_info.empty()
gesture_box = col_info.empty()
health_box = col_info.empty()

# ----------------- MEDIAPIPE -----------------
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.7,
    min_tracking_confidence=0.7
)
mp_draw = mp.solutions.drawing_utils

# ----------------- GEOMETRY -----------------
def distance(a, b):
    return math.sqrt((a.x - b.x)**2 + (a.y - b.y)**2)

def finger_open(lm, tip, pip, wrist):
    hand_size = distance(lm.landmark[0], lm.landmark[9])
    return distance(lm.landmark[tip], lm.landmark[wrist]) > \
           distance(lm.landmark[pip], lm.landmark[wrist]) + 0.15 * hand_size

def is_fist(lm):
    return not any([
        finger_open(lm, 8, 6, 0),
        finger_open(lm, 12, 10, 0),
        finger_open(lm, 16, 14, 0),
        finger_open(lm, 20, 18, 0)
    ])

def is_open_palm(lm):
    return all([
        finger_open(lm, 8, 6, 0),
        finger_open(lm, 12, 10, 0),
        finger_open(lm, 16, 14, 0),
        finger_open(lm, 20, 18, 0)
    ])

def is_index_up(lm):
    return (
        finger_open(lm, 8, 6, 0) and
        not finger_open(lm, 12, 10, 0) and
        not finger_open(lm, 16, 14, 0) and
        not finger_open(lm, 20, 18, 0)
    )

# ----------------- CAMERA -----------------
cap = cv2.VideoCapture(0)

danger = medical = sos = 0
last_alert = None

# ----------------- LOOP -----------------
while True:
    ret, frame = cap.read()
    if not ret:
        st.error("❌ Camera not accessible")
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    alert_text = "🟢 No Emergency"
    alert_color = "#2ecc71"
    alert_type = None

    if result.multi_hand_landmarks:
        lm = result.multi_hand_landmarks[0]
        mp_draw.draw_landmarks(frame, lm, mp_hands.HAND_CONNECTIONS)

        if is_fist(lm):
            danger += 1
            medical = sos = 0
            if danger > 25:
                alert_text = "🚨 DANGER DETECTED"
                alert_color = "#e74c3c"
                alert_type = "danger"

        elif is_open_palm(lm):
            medical += 1
            danger = sos = 0
            if medical > 25:
                alert_text = "🏥 MEDICAL EMERGENCY"
                alert_color = "#f39c12"
                alert_type = "medical"

        elif is_index_up(lm):
            sos += 1
            danger = medical = 0
            if sos > 25:
                alert_text = "🆘 SOS SIGNAL"
                alert_color = "#3498db"
                alert_type = "sos"

        else:
            danger = medical = sos = 0

    # ----------------- SOUND -----------------
    if alert_type and alert_type != last_alert:
        if alert_type == "danger":
            winsound.Beep(1000, 800)
        elif alert_type == "medical":
            winsound.Beep(900, 300)
            winsound.Beep(900, 300)
        elif alert_type == "sos":
            for _ in range(3):
                winsound.Beep(800, 200)
                time.sleep(0.1)
        last_alert = alert_type

    if alert_type is None:
        last_alert = None

    # ----------------- UI PANELS -----------------
    status_box.markdown(
        f"""
        <div style='padding:20px;
                    border-radius:12px;
                    background:{alert_color};
                    color:white;
                    text-align:center;
                    font-size:22px;
                    font-weight:bold;'>
            {alert_text}
        </div>
        """,
        unsafe_allow_html=True
    )

    gesture_box.markdown(
        """
        ### 🖐 Gesture Guide
        • ✊ Closed Fist → **Danger**  
        • ✋ Open Palm → **Medical**  
        • ☝ Index Finger → **SOS**
        """
    )

    health_box.markdown(
        """
        ### 🟢 System Status
        • Camera: Active  
        • Detection: Running  
        • Latency: Low
        """
    )

    frame_box.image(frame, channels="BGR")
    time.sleep(0.03)
