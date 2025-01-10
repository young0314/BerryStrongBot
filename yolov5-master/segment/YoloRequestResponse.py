from flask import Flask, request, jsonify
import os
import subprocess
import logging
import requests
import mysql.connector
from DBConfig import mysql_host, mysql_user, mysql_password, mysql_database
from datetime import datetime


app = Flask(__name__)
#로봇으로부터 받은 딸기 사진 YOLO 모델 적용시킨 후 결과값 리턴(X,Y좌표)
weights_path = "C:/strawberry_seg/best.pt"
logging.basicConfig(level=logging.DEBUG)

@app.route('/api', methods=['POST'])
def upload_image_and_predict():
    try:
        if 'sbimage' not in request.files:
            return jsonify({'error': 'Image not found in the request!'}), 400
        image = request.files['sbimage']

        if image.filename == '':
            return jsonify({'error': 'Image not selected!'}), 400
        file_path = os.path.join("C:/strawberry_seg/image", image.filename)
        image.save(file_path)

        result = run_model_and_send_result(file_path)
        print(result)
        return jsonify(result), 200

    except Exception as e:
        return jsonify({'error': f'Error uploading and predicting image: {str(e)}'}), 500


def run_model_and_send_result(image_path):
    try:
        process = subprocess.run(["python", "predict.py", "--weights", weights_path, "--source", image_path],
                                 capture_output=True, text=True)
        output = process.stdout.strip().replace('\n','').split("end")
        output_cleaned = [item for item in output if '\x1b[0m' not in item]

        save_to_database(output_cleaned)  # 결과를 MySQL 데이터베이스에 저장하는 함수 호출
        endpoint = "http://192.168.137.122:8080/hong_babo"
        payload = {'strawberry': output_cleaned}
        print(output_cleaned)

        try:
            response = requests.post(endpoint, json=payload)
        except requests.exceptions.ConnectionError as e:
            return {'error': 'Connection refused: Unable to establish connection to the server'}
        if response.status_code == 200:
            return {'strawberry': output_cleaned}
        else:
            return {'error': f'Error sending result to endpoint. Status code: {response.status_code}'}

    except subprocess.CalledProcessError as e:
        return {'error': f'Error running predict.py: {str(e)}'}

    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def save_to_database(output_cleaned):
    try:
        if not output_cleaned:  # output이 비어있는 경우 바로 반환
            return

        # MySQL 데이터베이스 연결
        db_connection = mysql.connector.connect(
            host=mysql_host,
            user=mysql_user,
            password=mysql_password,
            database=mysql_database
        )
        cursor = db_connection.cursor()

        # 결과를 MySQL에 삽입
        for item in output_cleaned:
            if item.strip():
                item_parts = item.split(',')
                x_coord = float(item_parts[0].split(':')[1].strip())
                y_coord = float(item_parts[1].split(':')[1].strip())
                ripe_percent = float(item_parts[2].split(':')[1].strip().replace('%', ''))
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 현재 시간을 가져와서 형식화

                # MySQL에 데이터 삽입
                sql = "INSERT INTO 수확관리 (x좌표, y좌표, 수확일, 숙도) VALUES (%s, %s, %s, %s)"
                val = (x_coord, y_coord,current_time, ripe_percent)
                cursor.execute(sql, val)
                db_connection.commit()

        # 연결 종료
        cursor.close()
        db_connection.close()

    except Exception as e:
        print(f'Error saving to database: {str(e)}')


if __name__ == '__main__':
    app.run(debug=True, host="192.xxx.xxx.xxx", port=8080)