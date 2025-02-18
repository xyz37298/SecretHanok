import cv2
import mediapipe as mp
import numpy as np
import joblib
import os
import requests
import base64
import time
from flask import Flask, render_template
from flask_cors import CORS
from flask_socketio import SocketIO, emit

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="gevent")

mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

# 현재 파일(backend.py)의 폴더 경로 가져오기
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 모델 파일을 절대 경로로 불러오기
model_path = os.path.join(BASE_DIR, "hand_gesture_recognition_model.pkl")
GDRIVE_URL = "https://drive.google.com/uc?export=download&id=1Aq_Q8jRu04al-S2x2ckwW-MWLpT8YXvk"

# 모델이 없으면 다운로드
if not os.path.exists(model_path):
    response = requests.get(GDRIVE_URL)
    with open(model_path, "wb") as f:
        f.write(response.content)

# 모델 로드
model = joblib.load(model_path)
print("✅ 모델 로드 완료!")

GESTURE_TEXTS = {
    "gesture_1": "내 손 안의 모래",
    "gesture_2": "간질 간질 신나",
    "gesture_3": "의문"
}

GESTURE_SUBTITLES = {
    "gesture_1": "나의 손은 모래성 쌓기의 MASTER! 기다려, 일루젼이어도 괜찮아. 한움큼 내가 확 쏟아버릴거야.",
    "gesture_2": "아! 생생해. 알알이 손가락 사이에 박힌 모래들이 까실까실, 생생하고 간지럽고 아프고 외롭고 신나.",
    "gesture_3": "근데 아니면 어떡하지? 에이, 그래도 괜찮아. 나는 우주의 별만큼 지을 표정이 많아. 그래도 어쩔 수 없잖아. 그래도 장난꾸러기처럼 해보는거야. 나는 MASTER니까! 그리고 살짝 서툰 수련생이야."
}

gesture_images = {
    "gesture_1": "static/images/gesture1.png",
    "gesture_2": "static/images/gesture2.png",
    "gesture_3": "static/images/gesture3.png"
}

gesture_sounds = {
    "gesture_1": "/static/sounds/gesture1.mp3",
    "gesture_2": "/static/sounds/gesture2.mp3",
    "gesture_3": "/static/sounds/gesture3.mp3",
}

is_playing = False
last_prediction = None #마지막으로 출력된 동작 저장

@app.route("/")
def index():
    return render_template("index.html")

@socketio.on("video_frame")
def handle_frame(data):
    global is_playing, last_prediction
    print("프레임 수신")
    
    frame_data = base64.b64decode(data.split(",")[1])
    print("프레임 데이터 크기:", len(frame_data))
    if len(frame_data) == 0:
        print("프레임 데이터가 비어있습니다!")
        return
    np_arr = np.frombuffer(frame_data, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    print("프레임 디코딩 완료:", frame.shape if frame is not None else "None")
    
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame)

    if not results.multi_hand_landmarks:
        print("손 인식 실패")
        return

    print("손 인식 성공")

    landmarks_list = []
    prediction = "알 수 없음"

    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            hand_data = []
            for lm in hand_landmarks.landmark:
                hand_data.append({"x": lm.x, "y": lm.y})
            landmarks_list.append(hand_data)

            # ✅ 모델을 사용하여 제스처 예측
            landmark_array = np.array([[lm.x, lm.y, lm.z] for lm in hand_landmarks.landmark]).flatten()
            if len(landmark_array) == model.n_features_in_:  # 모델 입력 크기와 맞는지 확인
                prediction = model.predict([landmark_array])[0]

    # 마커(손 위치)는 항상 업데이트
    emit("hand_landmarks", {"landmarks":landmarks_list})


    sound_url = gesture_sounds.get(prediction, "")

    #같은 제스쳐가 반복되면 이미지/텍스트/음성 갱신 x
    if not is_playing and prediction != last_prediction and prediction in GESTURE_TEXTS:
        last_prediction = prediction #마지막 출력된 동작 저장

        gesture_text = GESTURE_TEXTS.get(prediction, "손을 들어주세요")
        gesture_subtitle = GESTURE_SUBTITLES.get(prediction, "")
        image_url = gesture_images.get(prediction, "")

        emit("gesture_result", {
            "gesture": gesture_text,
            "subtitle": gesture_subtitle,
            "image_url":image_url,
            "sound": sound_url
        })

        # 일정 시간 후 음성이 끝났다고 가정하고 상태 초기화
        socketio.sleep(2)  # 💡 음성 길이에 맞게 조정 가능
        is_playing = False  # 음성이 끝나면 다시 업데이트 허용

if __name__ == "__main__":
    socketio.run(app, debug=True)
