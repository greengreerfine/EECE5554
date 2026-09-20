# PA1 - Getting Familiar with ROS 2

For PA1, I created a ROS 2 Jazzy Python package named `eece5554_pa1` inside the workspace:

`~/EECE5554/PA1/ros2_ws`

The package contains a publisher node (`talker.py`) and a subscriber node (`listener.py`).

## Talker

The talker publishes `std_msgs/msg/String` messages to the `/chatter` topic at 2 Hz.

The published message has the form:

`Robotics EECE 5554! Message <counter>`

## Listener

The listener subscribes to `/chatter`.

It modifies each received message by converting the string to uppercase and logs it in the form:

`I heard: ROBOTICS EECE 5554! MESSAGE <counter>`

## ROS 2 Tools Used

I also used ROS 2 command-line and GUI tools including:

* `ros2 node list`
* `ros2 topic list`
* `ros2 topic info`
* `ros2 topic echo`
* `rqt_graph`
* `turtlesim`

For the turtlesim exercise, I used `turtle_teleop_key` to control the turtle and saved the resulting doodle as `ZHANG_turtle.png`.

## Verification

The PA1 verification script successfully confirmed:

* ROS 2 Jazzy installation
* required build tools
* workspace and package structure
* successful colcon build
* registered talker and listener executables
* `/chatter` publisher
* listener operation
* modified listener string
* turtlesim screenshot
* Git hygiene
