# BerryStrongBot
딸기를 인식해서 수확하는 로봇 프로젝트

## 💻 프로젝트 소개
- YOLOv5와 DOFBOT을 사용해 딸기를 수확하는 프로젝트
<br>

## ⏰ 개발기간
- 2023.09.13 ~ 2024.01.09

## 🙋 구성원
- 배윤재 : HW
- 홍서영 : SW(학습, 좌표 계산, 서버)
- 유성경 : SW(라벨링, 숙성도 계산)

## ⚙️ 개발 환경
- python3.9
- ubuntu18.04
- Database : MySQL
- HardWare : DofBot, Jetson Nano
- Train : Google colab
- YOLOv5
- ROS

## 📃 기획 배경
- 초고령화로 인한 농촌지역의 노동력 부족문제를 해결하기 위해 수확로봇 프로젝트를 기획함
- 과채 중 노동시간이 가장 많은 딸기를 채택

## 📌 주요 기능
#### 익은/안익은 딸기 학습 
- 익은 딸기만을 수확하기 위해 두가지 유형의 모델을 학습
  
#### 익은 딸기의 숙성도 계산
- 정확한 수확 여부를 정하기 위해서 한 번 더 딸기의 익음 정도를 구분함
- 딸기사진을 RGB값으로 변환해서 계산
https://github.com/young0314/BerryStrongBot/blob/30720c801a248f413796bf9f7404279beba34faa/yolov5-master/segment/predict.py#L214-L232

#### 딸기 꼭짓점 좌표 계산과 수확 순서 지정
- 로봇팔이 딸기를 수확하기 위해서 yolo 바운딩 박스의 위치에서 수확지점인 상단 중앙 부분 좌표(x,y)를 계산
- 수확 순서는 왼쪽을 기준으로 딸기에 번호를 부여
https://github.com/young0314/BerryStrongBot/blob/30720c801a248f413796bf9f7404279beba34faa/yolov5-master/segment/predict.py#L233-L249

#### 좌표 전달과 DB에 저장
- 계산한 좌표를 하드웨어에 전달하며 수확한 데이터(좌표, 수확일)들을 저장
https://github.com/young0314/BerryStrongBot/blob/58d96f6fe7f646359755b707d07b817b3dce1731/yolov5-master/segment/YoloRequestResponse.py

#### 숙성도 70% 이상일 때 로봇팔로 수확
- 상품을 판매하기에 적합한 숙성도인 70%를 기준으로 수확

## 시연
### 딸기 인식
![Image](https://github.com/user-attachments/assets/c20dac3e-00f5-41c2-a215-fac0bdfc631f)

### 딸기 수확
![로봇 수확](https://github.com/user-attachments/assets/6ecdd7c2-6af8-4a05-a530-2a850d6abe04)

