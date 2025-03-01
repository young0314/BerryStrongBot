import cv2
import math
import time
import os
import requests
from requests.exceptions import RequestException
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import threading
from Arm_Lib import Arm_Device

#딸기 이미지를 저장할 디렉터리
save = "sbimage"
os.makedirs(save, exist_ok=True)

app = Flask(__name__)

#딸기 감지 및 로봇 팔 제어 클래스
class sbDetection:
    def __init__(self):
        #변수 및 로봇팔 초기화
        self.image_captured = False
        self.start_time = time.time()
         # 로봇팔 객체 생성
        self.Arm = Arm_Device()
        self.target_coordinates = None
        self.distance_px = 0
        #카메라 좌표 동일 설정
        self.camera_resolution_x = 100
        self.camera_resolution_y = 100
        #로봇팔 좌표 범위 설정
        self.robot_arm_range_x = 100
        self.robot_arm_range_y = 100
        time.sleep(0.1)

        #로봇팔 초기 모터 설정
        self.initial_angles = [90, 90, 20, 20, 90, 130]
        
        for motor_id, initial_angle in enumerate(self.initial_angles, start=1):
            self.Arm.Arm_serial_servo_write(motor_id, initial_angle, 500)

        #로봇팔 관절 길이
        self.l1 = 0
        self.l2 = 6.5
        self.l3 = 8.5
        self.l4 = 8.5

    #카메라 좌표를 로봇팔의 좌표로 변환
    def convert_camera_to_robot_coordinates(self, x_camera, y_camera):
        camera_resolution_x = 640
        camera_resolution_y = 480
        robot_arm_range_x = 100
        robot_arm_range_y = 100
        
        #변환 계산
        x_robot = int(((x_camera + 43) / camera_resolution_x) * robot_arm_range_x)
        y_robot = int((((camera_resolution_y - y_camera) - 40) / camera_resolution_y) * robot_arm_range_y)
        
        return x_robot, y_robot

     #로봇팔을 특정 x, y좌표로 이동
    def move_to_xyz(self, x, y):
        l1 = 0
        l2 = 6.5
        l3 = 8.5
        l4 = 8.5
        
        #역기구학 각도 계산
        theta1 = math.atan2(y, x)
        d_xy = math.sqrt(x**2 + y**2)
        
        x_end = x - l4 * math.cos(theta1)
        y_end = y - l4 * math.sin(theta1)
        
        l_arm = math.sqrt(x_end**2 + y_end**2)
        
        if l_arm > l2 + l3:
            l_arm = l2 + l3
            
            cos_theta2 = (l_arm**2 - l2**2 - l3**2) / (2 * l2 * l3)
            theta2 = math.acos(cos_theta2)
            
            cos_theta3 = ((l_arm**2 - l2**2 - l3**2) / (-2 * l2 * l3))
            theta3 = math.pi - math.acos(cos_theta3)
            
            theta4 = math.atan2(y_end, x_end)
            
            #로봇팔 서보 모터에 각도 명령
            self.Arm.Arm_serial_servo_write(1, math.degrees(theta1), 500)
            self.Arm.Arm_serial_servo_write(2, math.degrees(theta2), 500)
            self.Arm.Arm_serial_servo_write(3, math.degrees(theta3), 500)
            self.Arm.Arm_serial_servo_write(4, math.degrees(theta4), 500)
            
            print("Moved to X:", x, "Y:", y)
            print("Theta1:", math.degrees(theta1))
            print("Theta2:", math.degrees(theta2))
            print("Theta3:", math.degrees(theta3))
            print("Theta4:", math.degrees(theta4))

    #딸기 감지 및 제어 메인 함수
    def main(self):
        cam = cv2.VideoCapture(0)

        #딸기 인식 데이터 파일 로드
        strawberry_cascade = cv2.CascadeClassifier('strawberry_classifier.xml')
        camera_width = 640
        camera_height = 480
        camera_angle = 100
        camera_focal = 500

        try:
            while True:
                _, frame = cam.read()

                #그레이스케일 변환 후 딸기 감지
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                strawberries = strawberry_cascade.detectMultiScale(gray_frame, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

                #카메라와 딸기 사이의 거리 측정
                for (x, y, w, h) in strawberries:
                    sb_diameter_px = (w + h) / 2
                    self.distance_px = (camera_width * camera_focal) / (2 * sb_diameter_px * math.tan(math.radians(camera_angle / 2)))
                    #카메라 보정값
                    correction_factor = 85
                    self.distance_px += correction_factor

                    #감지된 딸기 주위에 사각형 및 원 표시
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    cv2.circle(frame, (int(x + w / 2), int(y + h / 2)), 3, (255, 0, 0), -1)
                    
                    box_center_x = x + w // 2
                    box_top_center_y = y

                    screen_width = frame.shape[1]
                    screen_height = frame.shape[0]
                    normalized_x = box_center_x * 100 // screen_width
                    normalized_y = box_top_center_y * 100 // screen_height
                    
                    cv2.putText(frame, f"({normalized_x}, {normalized_y})", (box_center_x - 20, box_top_center_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                    cv2.putText(frame, f"Distance: {self.distance_px:.2f} px", (x + w + 10, y + h // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                cv2.imshow("hing", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("w"):
                    image_path = self.capture(cam, width=800, height=542)
                    print("찰칵")
                    self.strawberry_send(image_path)
                    print(f"Distance: {self.distance_px:.2f} px")

                if key == ord("q"):
                    break

        except KeyboardInterrupt:
            pass

        finally:
            cam.release()
            cv2.destroyAllWindows()

    #이미지 캡처 및 저장
    def capture(self, cam, width, height):
        timestamp = time.strftime("%Y%m%d%H%M%S")
        file_name = f"{timestamp}.jpg"
        image_path = os.path.join(save, file_name)

        _, sbimage = cam.read()
        sbimage_resized = cv2.resize(sbimage, (width, height))
        cv2.imwrite(image_path, sbimage_resized)

        return image_path

    #이미지를 서버로 전송
    def strawberry_send(self, image_path):
        print("post loading")
        try:
            url = 'http://192.168.137.218:8080/api'

            files = {'sbimage': open(image_path, 'rb')}
            response = requests.post(url, files=files)
            response.raise_for_status()

            print("post success")

        except (RequestException, Exception) as e:
            print(f"post error: {e}")
            raise

instance = sbDetection()

#POST 요청 처리
@app.route('/hong_babo', methods=['POST'])
def upload_file():
    try:
        json_data = request.get_json()

        print(json_data)

        if not isinstance(json_data, dict):
            return jsonify({'Error': 'Invalid JSON data'}), 400

        strawberries = json_data.get('strawberry')
        if not isinstance(strawberries, list):
            return jsonify({'Error': 'Invalid strawberry data format'}), 400

        #좌표 및 익은 정도
        for strawberry_info in strawberries:
            try:
                parts = strawberry_info.split(',')
                x_str = parts[0].split(':')[1].strip()
                y_str = parts[1].split(':')[1].strip()
                ripeness_str = parts[2].split(':')[1].strip()
                ripeness = float(ripeness_str[:-1])

                x_camera = None
                y_camera = None

                #익은 정도가 50% 이상인 경우만 좌표 설정
                if ripeness >= 50:
                    x_camera = float(x_str)
                    y_camera = float(y_str)

                #좌표 설정 후 로봇 좌표 변환 및 이동 명령
                if x_camera is not None and y_camera is not None:
                    x_robot, y_robot = instance.convert_camera_to_robot_coordinates(x_camera, y_camera)
                    instance.move_to_xyz(x_robot, y_robot)
                else:
                    print("Strawberry not ripe enough")

            except (ValueError, IndexError) as e:
                print(f"Error processing strawberry info: {e}")

        return jsonify({'Result': 'Success'}), 200
    except Exception as e:
        print(e)
        return jsonify({'Error': f'Internal Server Error: {str(e)}'}), 500

def run_flask_app():
    app.run(host='192.168.137.122', port=8080)

if __name__ == "__main__":
    t_flask = threading.Thread(target=run_flask_app)
    t_flask.daemon = True
    t_flask.start()

    instance.main()
