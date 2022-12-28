#!/usr/bin/env python
# coding=utf-8
import rospy
from sensor_msgs.msg import JointState
from geometry_msgs.msg import Twist
import sys, select, termios, tty

msg = """
Control Your Robot!
---------------------------
Moving around:
   u    i    o
   j    k    l
   m    ,    .

Moving arm:
   1    2    3   4   5   6   
   q    w    e   r   t   y   

a/z : increase/decrease max speeds by 10%
s/x : increase/decrease only linear speed by 10%
d/c : increase/decrease precision by 0.05
space key : reset
k : force stop
f : special position
anything else : stop smoothly
b : switch to OmniMode/CommonMode
precision is not less than or equal to zero
CTRL-C to quit
"""
Omni = 0 #全向移动模式

precision = 0.05 #默认精度(rad)

#键值对应转动方向
rotateBindings = {
        '1':(1,1),
        'q':(1,-1),
        '2':(2,1),
        'w':(2,-1),
        '3':(3,1),
        'e':(3,-1),
        '4':(4,1),
        'r':(4,-1),
        '5':(5,1),
        't':(5,-1),
        '6':(6,1),
        'y':(6,-1)
        }

#键值对应精度增量
precisionBindings={
        'd':0.01,
        'c':-0.01
          }

#键值对应移动/转向方向
moveBindings = {
        'i':( 1, 0),
        'o':( 1,-1),
        'j':( 0, 1),
        'l':( 0,-1),
        'u':( 1, 1),
        ',':(-1, 0),
        '.':(-1, 1),
        'm':(-1,-1)
           }

#键值对应速度增量
speedBindings={
        'a':(1.1,1),
        'z':(0.9,1),
        's':(1,1.1),
        'x':(1,0.9)
          }

#获取键值函数
def getKey():
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''

    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)
    return key

speed = 0.2 #默认移动速度 m/s
turn  = 1   #默认转向速度 rad/s
#以字符串格式返回当前控制精度
def prec(speed,turn,precision):
    return "currently:\tspeed %s\tturn %s\ttprecision %s " %(speed,turn,precision)
def limit1():
    if joints[rotateBindings[key][0]-1]>1.57:
             joints[rotateBindings[key][0]-1]=1.57
    elif joints[rotateBindings[key][0]-1]<-1.57:
             joints[rotateBindings[key][0]-1]=-1.57
def limit2():
    if joints[rotateBindings[key][0]]>0.7:
             joints[rotateBindings[key][0]]=0.7
    elif joints[rotateBindings[key][0]]<-0.3 :
             joints[rotateBindings[key][0]]=-0.3
def limit3():
    if joints[rotateBindings[key][0]-1]>0.7:
             joints[rotateBindings[key][0]-1]=0.7
    elif joints[rotateBindings[key][0]-1]<-0.3:
             joints[rotateBindings[key][0]-1]=-0.3           
#主函数
if __name__=="__main__":
    settings = termios.tcgetattr(sys.stdin) #获取键值初始化，读取终端相关属性
    
    rospy.init_node('arm_teleop') #创建ROS节点
    pub_arm = rospy.Publisher('/joint_states', JointState, queue_size=5) #创建机械臂状态话题发布者
    pub_vel = rospy.Publisher('/cmd_vel', Twist, queue_size=5) #创建速度话题发布者

    #关节1-6对应弧度状态
    joints = [0,0,0,0,0,0,0]

    """机械臂关节初始化"""
    jointState = JointState() #创建ROS机械臂装态话题消息变量
    jointState.header.stamp = rospy.Time.now()
    jointState.name=["joint1","joint2","joint3","joint4","joint5","joint6","joint8"]
    jointState.position=joints
    pub_arm.publish(jointState) #ROS发布机械臂状态话题
    
    """底盘控制初始化"""
    twist = Twist() #创建ROS速度话题变量
    x      = 0   #前进后退方向
    th     = 0   #转向/横向移动方向
    count  = 0   #键值不再范围计数
    target_speed = 0 #前进后退目标速度
    target_turn  = 0 #转向目标速度
    target_HorizonMove = 0 #横向移动目标速度
    control_speed = 0 #前进后退实际控制速度
    control_turn  = 0 #转向实际控制速度
    control_HorizonMove = 0 #横向移动实际控制速度
    try:
        print(msg) #打印控制说明
        print(prec(speed,turn,precision)) #打印当前速度,精度
        while(1):
            key = getKey() #获取键值

            #切换是否为全向移动模式，全向轮/麦轮小车可以加入全向移动模式
            if key=='b':               
                Omni=~Omni
                if Omni: 
                    print("Switch to OmniMode")
                    moveBindings['.']=[-1,-1]
                    moveBindings['m']=[-1, 1]
                else:
                    print("Switch to CommonMode")
                    moveBindings['.']=[-1, 1]
                    moveBindings['m']=[-1,-1]

            #判断键值是否在移动/转向方向键值内
            if key in moveBindings.keys():
                x  = moveBindings[key][0]
                th = moveBindings[key][1]
                count = 0

            #判断键值是否在速度增量键值内
            elif key in speedBindings.keys():
                speed = speed * speedBindings[key][0]
                turn  = turn  * speedBindings[key][1]
                count = 0
                print(prec(speed,turn,precision)) #速度发生变化，打印出来

            #'k',相关变量置0
            elif key == 'k' :
                x  = 0
                th = 0
                control_speed = 0
                control_turn  = 0
                HorizonMove   = 0
                count = 0
            # elif key == '6' or key == 'y':

            #判断键值是在控制机械臂运动的键值内
            elif key in rotateBindings.keys():
                count = 0
                if key == '6' or key == 'y':
                    joints[rotateBindings[key][0]-1] = joints[rotateBindings[key][0]-1] + precision*rotateBindings[key][1]
                    limit3()
                    joints[rotateBindings[key][0]] = joints[rotateBindings[key][0]] + precision*rotateBindings[key][1]
                    limit2()
                else:
                    joints[rotateBindings[key][0]-1] = joints[rotateBindings[key][0]-1] + precision*rotateBindings[key][1]
                    limit1()
            #判断键值是否在精度增量键值内
            elif key in precisionBindings.keys():
                count = 0
                if (precision+precisionBindings[key])<=0 or (precision+precisionBindings[key])>0.1:
                    pass
                else:
                    precision+=precisionBindings[key]
                print(prec(speed,turn,precision)) #精度发生变化，打印出来

            #空格键机械臂复位
            elif key == ' ':
                joints = [0,0,0,0,0,0,0]
                count = 0

            #f键收起夹爪
            elif key=='f':
                joints = [0,0.57,1.57,1.3,0,0.6,0.6]
                count = 0

            #ctrl+c退出循环
            elif (key == '\x03'):
                break

            #长期识别到不明键值，相关变量置0
            else:
                count+=1
                if count>4:
                    x  = 0
                    th = 0
            

            """底盘速度话题消息发布"""
            #根据速度与方向计算目标速度
            target_speed = speed * x
            target_turn  = turn * th
            target_HorizonMove = speed*th

            #平滑控制，计算前进后退实际控制速度
            if target_speed > control_speed:
                control_speed = min( target_speed, control_speed + 0.1 )
            elif target_speed < control_speed:
                control_speed = max( target_speed, control_speed - 0.1 )
            else:
                control_speed = target_speed

            #平滑控制，计算转向实际控制速度
            if target_turn > control_turn:
                control_turn = min( target_turn, control_turn + 0.5 )
            elif target_turn < control_turn:
                control_turn = max( target_turn, control_turn - 0.5 )
            else:
                control_turn = target_turn

            #平滑控制，计算横向移动实际控制速度
            if target_HorizonMove > control_HorizonMove:
                control_HorizonMove = min( target_HorizonMove, control_HorizonMove + 0.1 )
            elif target_HorizonMove < control_HorizonMove:
                control_HorizonMove = max( target_HorizonMove, control_HorizonMove - 0.1 )
            else:
                control_HorizonMove = target_HorizonMove
         
            #根据是否全向移动模式，给速度话题变量赋值
            if Omni==0:
                twist.linear.x  = control_speed; twist.linear.y = 0;  twist.linear.z = 0
                twist.angular.x = 0;             twist.angular.y = 0; twist.angular.z = control_turn
            else:
                twist.linear.x  = control_speed; twist.linear.y = control_HorizonMove; twist.linear.z = 0
                twist.angular.x = 0;             twist.angular.y = 0;                  twist.angular.z = 0

            pub_vel.publish(twist) #ROS发布速度话题

            """机械臂话题消息发布"""
            #给joint_states话题赋予消息
            jointState.header.stamp = rospy.Time.now()
            jointState.name=["joint1","joint2","joint3","joint4","joint5","joint6","joint8"]
            jointState.position=joints

            pub_arm.publish(jointState) #ROS发布关节状态话题

    #运行出现问题则程序终止并打印相关错误信息
    except Exception as e:
        print(e)

    #程序结束前打印消息提示
    finally:
        twist = Twist()
        twist.linear.x = 0;  twist.linear.y = 0;  twist.linear.z = 0
        twist.angular.x = 0; twist.angular.y = 0; twist.angular.z = 0
        pub_vel.publish(twist)
        print("Keyboard control off")

    #程序结束前设置终端相关属性
    termios.tcsetattr(sys.stdin, termios.TCSADRAIN, settings)

