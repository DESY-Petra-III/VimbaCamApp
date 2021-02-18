# Vimba Camera Project

This is a simple project with a PyQt application accessing GiGE or USB cameras through [VimbaSDK](https://www.alliedvision.com/en/products/software.html) of [Allied Vision](https://www.alliedvision.com/). 

The project is made with high pressure community (diamon anvil cell) in mind, where a position of a laser, size of a sample chamber, position of the sample inside a sample chamber is of relevance for various experiments experiment.

Unlike the original VimbaViewer, the program provides a  functionality limited, as the most often used by a synchrotron beamline operator.


## Project Folders

The project has two folders:

 - **code** - the PyQt application itself
 - **example_remote_acesss** - code illustrating remote access to the application using [ZMQ](https://zeromq.org/languages/python/) library.
 - 

## Principle of operation

The program is started using keys:

	python3 VimbaApp.py --id DEV_1AB22C004C6D --zmq tcp://*:5555

 - **--id DEV_1AB22C004C6D**
 - **--zmq tcp://*:5555**

The first key indicates a camera device unique identifier.
The second key sets up a ZMQ server listening for remote commands.

If the camera is online, the user would be able to start frame acquisition, change gain and exposure.

Some indication is provided: 

 - Center of the frame
 - Marker - indicator with adjustable shape, position, color

Marker size, color, frame size, visibility for the frame and marker are saved into a configuration file.

The program is implemented to be used in a *userland* environment, when access to the administrator user is limited.

## Libraries and requirenments
On top of the standard python3 libraries, additional libraries are required:

	pip install numpy PyQt5 qtpy opencv-python

Vimba API libraries are available within [VimbaSDK](https://www.alliedvision.com/en/products/software.html)  as well as the corresponding documentation describing the details of SDK installation.

Windows users should setup *VIMBA_HOME* environment variable, while LINUX users take advantage of *GENICAM_GENTL64_PATH* environment variable to locate corresponding libraries.