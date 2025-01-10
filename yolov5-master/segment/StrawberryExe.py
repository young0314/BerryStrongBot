import subprocess

#웹캠 테스트 실행코드(사용X)
command = "python predict.py --weights C:/strawberry_seg/best.pt --conf 0.7 --img 640 --source 0"

process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
subprocess.run(command, shell=True)
