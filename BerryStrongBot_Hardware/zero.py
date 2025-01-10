import time
from Arm_Lib import Arm_Device

Arm = Arm_Device()
time.sleep(1)

def main():
    Arm.Arm_serial_servo_write6(90, 90, 80, 20, 90, 180, 500)
    time.sleep(1)
    
try :
    main()
except KeyboardInterrupt:
    print(" Program closed! ")

del Arm 