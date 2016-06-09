15-112 Term Project, Fall 2015 Session
Jessie Li

Project: aMAZEing

***FOR THE PURPOSES OF THIS ONLINE CODE DEMO, THE GAME DATA FILES HAVE BEEN EXCLUDED***


This project is a three-dimensional maze game called, aMAZEing. 
The structures for the game are built in Blender 2.76b, and the game itself is played in the game engine Panda3D. 
The code for the project was written in Python 3.

The download for Blender 2.76b can be found on the Internet, at the URL  "https://www.blender.org/download/".
The download for Panda3D software can be found at the URL "https://www.panda3d.org/download.php". 

For the purposes of this project, which was created and run on a MacBook Air, OS X El Capitan, the standard Panda3D at the URL provided did not run; the software that the program was run on can be found at the URL "https://www.panda3d.org/blog/update-for-mac-os-x-el-capitan/". Panda3D download comes with its own version of Python, which accesses all the Panda3D modules; the Panda3D file must be run in the Panda3D version of Python (called ppython). However, this project was written and run in the Python text editor Sublime, which can be downloaded at the URL "http://www.sublimetext.com/3". To connect the Sublime Text editor to the ppython modules (on a MacBook), open Sublime, open "Preferences", and open "Browse Packages". In the "Packages" folder, open the "User" folder, and open the python file named "python-with-ui-options.py", and change the value of the key 'cmd' in self.window.run_command argument dictionary to " [ "ppython", "-i\", "-u\", "$file\"] ". Sublime Text should then be able to run Panda3D modules.

There are two main Python files in the project; the first, called mazeGenorator.py, is a Blender script that generates mazes. Mazes, in this game, are a three dimensional cube/rectangular prism, made up of layers, each layer forming its own individual maze. In each level, there is a location where a player can move from the previous level to the current level, and then another location where the player can move from the current level to the next level; in effect, these locations are the "start" and "end" locations in the Maze. 

The Blender script can be run in the Blender Text Editor view, and it will randomly generate a each layer of the maze, randomly generate the "start" and "end" locations in each maze, and eventually join the layers together to form one large three-dimensional multi-level maze. To export the mazes, the add-on YABEE (Yet Another Blender EGG Exporter) must be downloaded (available at "https://code.google.com/p/yabee/downloads/list") and the add-on must be enabled, in the User Preferences > Add-Ons view. 
	
Once YABEE is installed, the maze can be exported in the Info View, under File > Export > Panda3D (.egg). This will export the maze shape as an .egg file. This step potentially could have been done in the script; however, the complexity of the export and subsequent import for the overall program is very high, so this step was done manually. In the project file, there are 11 samples of randomly generated maze .egg files in the mazeModels directory, which, in the Panda3D program, are chosen at random.

To play the actual game, the file mazeAnimation.py can be run in Sublime (after connecting to ppython). The player is a blue/green sphere that rolls around the maze, and the viewpoint is first-person. The point of the game is to reach the end of the maze (before the timer is up, if timer mode is selected.)\
	Other files in the project file include a file named ball.egg (the structure for the player object), a directory named ballTex (containing images used for texture generation on the player), a directory named wallTex (containing images used for texture generation on the maze walls), and a direction named splashScreens, which contains images of the splash screens.
