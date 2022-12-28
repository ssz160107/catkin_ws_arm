# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import stat
import sys

# find the import for catkin's python package - either from source space or from an installed underlay
if os.path.exists(os.path.join('/opt/ros/melodic/share/catkin/cmake', 'catkinConfig.cmake.in')):
    sys.path.insert(0, os.path.join('/opt/ros/melodic/share/catkin/cmake', '..', 'python'))
try:
    from catkin.environment_cache import generate_environment_script
except ImportError:
    # search for catkin package in all workspaces and prepend to path
    for workspace in '/home/ssz/wheeltec_arm/devel;/home/ssz/ws_rmrobot/devel;/home/ssz/catkin_ws_niryo_ned/devel;/home/ssz/demo19_learning_ros/devel;/home/ssz/demo18_action/devel;/home/ssz/demo16_launch_test/devel;/home/ssz/demo15_server_client/devel;/home/ssz/demo14_pub_sub/devel;/home/ssz/demo13_ws/devel;/home/ssz/demo12_ws/devel;/home/ssz/demo11_ws/devel;/home/ssz/demo10_ws/devel;/home/ssz/demo09_ws/devel;/home/ssz/demo08_ws/devel;/home/ssz/demo06_ws/devel;/opt/ros/melodic'.split(';'):
        python_path = os.path.join(workspace, 'lib/python2.7/dist-packages')
        if os.path.isdir(os.path.join(python_path, 'catkin')):
            sys.path.insert(0, python_path)
            break
    from catkin.environment_cache import generate_environment_script

code = generate_environment_script('/home/ssz/catkin_ws_arm/devel/env.sh')

output_filename = '/home/ssz/catkin_ws_arm/build/catkin_generated/setup_cached.sh'
with open(output_filename, 'w') as f:
    # print('Generate script for cached setup "%s"' % output_filename)
    f.write('\n'.join(code))

mode = os.stat(output_filename).st_mode
os.chmod(output_filename, mode | stat.S_IXUSR)
