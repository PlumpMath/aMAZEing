# Maze Animation- Jessie Li
# December 8, 2015
# Adapted from Ryan Myers - Panda3D Roaming-Ralph Demo
# With code from Josh Enes - Panda3D Portal Culling Demo

# This is a ppython file, a python file that runs in joint with 
# Panda3D software. The file creates an rendering of a three-dimensional,
# multi-level, randomly-generated maze, in which a player can move around
# to try and solve. The maze is loaded from an .egg file, which was created and 
# exported by the file mazeRandomizer.py, a script that creates a randomly
# generated maze using the software Blender.

# Import needed modules
import direct.directbase.DirectStart

from panda3d.core import PerspectiveLens
from panda3d.core import NodePath 
from panda3d.core import TexGenAttrib
from panda3d.core import TextureStage
from panda3d.core import TransparencyAttrib
from panda3d.core import TextNode
from panda3d.core import Material
from panda3d.core import LRotationf
from panda3d.core import AmbientLight
from panda3d.core import DirectionalLight
from panda3d.core import TextNode
from panda3d.core import Vec3, Vec4
from panda3d.core import Filename
from panda3d.core import PandaNode
from panda3d.core import Camera

from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage

from direct.gui.DirectGui import *

from direct.showbase.DirectObject import DirectObject

from direct.interval.MetaInterval import Sequence
from direct.interval.MetaInterval import Parallel

from direct.interval.LerpInterval import LerpPosInterval
from direct.interval.LerpInterval import LerpHprInterval
from direct.interval.LerpInterval import LerpFunc

from direct.interval.FunctionInterval import Func
from direct.interval.FunctionInterval import Wait

from pandac.PandaModules import CollisionHandlerQueue 
from pandac.PandaModules import CollisionNode
from pandac.PandaModules import CollisionSphere
from pandac.PandaModules import CollisionTraverser
from pandac.PandaModules import BitMask32

from direct.task.Task import Task

import random, sys, os, math

MESSAGES = []

def addInstructions(pos, msg):
    #adds instructions to the screen
    return OnscreenText(text=msg, style=1, fg=(0,0,0,1),
                        pos=(-1.3, pos), align=TextNode.ALeft, scale = .05)

def addTitle(text):
    #puts title of game on the screen
    return OnscreenText(text=text, style=1, fg=(0,0,0,1),
                        pos=(1.3,-0.95), align=TextNode.ARight, scale = .07)

def addNotification(txt):
    #adds a notification to the screen
    tex = OnscreenText(text=txt, style=1, fg= (1, 1, 1, 1), 
                                        align=TextNode.ACenter, pos=(0, .9))
    MESSAGES.append(tex)

def deleteNotifications():
    #deletes all on-screen notifications
    for msg in MESSAGES:
        msg.destroy()

class SplashScreen(object):
    #class SplashScreen, which loads a splash screen

    def __init__(self):
        #initialization of a splash screen - nothing happens
        #must request type of splash screen
        pass

    def loading(self):
        #splash screen for loading
        self.image = OnscreenImage(
            image = "/Users/jianwei/Documents/School/Freshman/Semester1/15-112/TERMPROJECT/Project/splashScreens/loading.png", 
                                            pos = (0, 0, 0), parent=render2d)
        self.renderFrame()
        self.image.destroy()

    def introduction(self):
        #splash screen for an introduction
        self.image1 = OnscreenImage(
            image = "/Users/jianwei/Documents/School/Freshman/Semester1/15-112/TERMPROJECT/Project/splashScreens/welcome.png",
                                            pos = (0, 0, 0), parent=render2d)
        self.renderFrame()
        self.image1.destroy()

    def mode(self):
        #splash screen for asking for mode
        self.image3 = OnscreenImage(
            image="/Users/jianwei/Documents/School/Freshman/Semester1/15-112/TERMPROJECT/Project/splashScreens/mode.png", 
                                        pos = (0, 0, 0), parent=render2d)

        for i in range(2):
            self.renderFrame()
        self.image3.destroy()

    def lose(self):
        #splash screen for if time runs out
        self.image4 = OnscreenImage(
            image="/Users/jianwei/Documents/School/Freshman/Semester1/15-112/TERMPROJECT/Project/splashScreens/lose.png", 
                                        pos = (0, 0, 0), parent=render2d)

        for i in range(2):
            self.renderFrame()
        self.image4.destroy()

    def win(self):
        #splash screen for a win
        self.image2 = OnscreenImage(
            image="/Users/jianwei/Documents/School/Freshman/Semester1/15-112/TERMPROJECT/Project/splashScreens/winning.png", 
                                        pos = (0, 0, 0), parent=render2d)

        for i in range(2):
            self.renderFrame()
        self.image2.destroy()

    def renderFrame(self):
        #renders the frame for a bit
        reps = 50
        for i in range(reps):
            base.graphicsEngine.renderFrame()
            base.graphicsEngine.renderFrame()
            base.graphicsEngine.renderFrame()

class World(DirectObject):
    #class World, extends DirectObject, builds the world to play the game

###################### INITIALIZATIONS #########################################
    def __init__(self):

        mySplashScreen = SplashScreen()
        mySplashScreen.loading()
        mySplashScreen.introduction()
        self.promptMode()

        self.turnWallNotification()

        ##### Creating Scene #####
        self.createBackground()
        self.loadWallModel()
        self.loadBallModel()
        self.setCamera()
        self.createLighting()

        ##### Create Controls #####
        self.createKeyControls()
        self.keyMap = {"left":0, "right":0, "forward":0, "backward":0, "drop":0}

        ##### Task Manager #####
        timer = 0.2
        taskMgr.doMethodLater(timer, self.traverseTask, "tsk_traverse")
            #scans for collisions every 0.2 seconds
        taskMgr.add(self.move,"moveTask")
            #constant smooth movement

        ##### Collisions #####
        self.createBallColliderModel()
        self.disableForwardMovement = False
        self.disableBackwardMovement = False
        self.disableLeftMovement = False
        self.disableRightMovement = False

        ##### Game state variables #####
        self.isMoving = False
        self.isDropping = False 
        self.camAngle = math.pi/2
        self.direction = "W" #constant; does not change with relativity
        self.drop = False

        self.levelHeight = 2.1
        self.level = 0
        self.maxLevel = 6
        self.currentHeight = 13.302
        self.cameraHeight = 0.2
        self.mode = None
        self.timer = ""

        ##### Views #####
        self.xray_mode = False
        self.collision_mode = False
        self.wireframe = False

        ##### On-Screen Text #####
        self.title = addTitle("aMAZEing")
        self.instructions = OnscreenText(text="[ i ]: Toggle Instructions", 
                style=1, fg=(0, 0, 0, 1), pos=(1.3, 0.95), 
                align=TextNode.ARight, scale=0.05)
        self.instr = []
        self.messages = []
        self.levelText = OnscreenText(text= "Level = " + str(self.level), 
                style=1, fg=(0, 0, 0, 1), pos=(-1.3, -0.95), 
                align=TextNode.ALeft, scale=0.07)
        self.directionText = OnscreenText(text="Direction = " + self.direction,
                style=1, fg=(0, 0, 0, 1), pos=(-1.3, -0.85),
                align=TextNode.ALeft, scale=0.07)

        self.timerText = OnscreenText(text= self.timer, 
                style=1, fg=(1, 1, 1, 1), pos=(1.3, 0.85), 
                align=TextNode.ARight, scale=0.07)
    
    def setKey(self, key, value):
        #records the state of the arrow keys
        self.keyMap[key] = value

    ###################### Onscreen Text #######################################

    def postInstructions(self):
        #posts the instructions onto the screen

        inst1 = addInstructions(0.95, "[ESC]: Quit")
        self.instr.append(inst1)
        inst2 = addInstructions(0.90,  "[Left Arrow]: Turn Left")
        self.instr.append(inst2)
                               
        inst3 = addInstructions(0.85, "[Right Arrow]: Turn Right")
        self.instr.append(inst3)
                                
        inst4 = addInstructions(0.80, "[Up Arrow]: Move Ball Forward")
        self.instr.append(inst4)
                                
        inst5 = addInstructions(0.75,  "[Down Arrow]: Move Ball Backwards")
        self.instr.append(inst5)
                               
        inst6 = addInstructions(0.70,
                            "[Space]: Drop Levels (if level drop is availale)")
        self.instr.append(inst6)
                               
        inst7 = addInstructions(0.60,  "[x]: Toggle XRay Mode")
        self.instr.append(inst7)
                               
        inst8 = addInstructions(0.55, "[c]: Toggle Collision Mode")
        self.instr.append(inst8)
                                
        inst9 = addInstructions(0.50, "[z]: Toggle Wireframe")
        self.instr.append(inst9)

        inst10 = OnscreenText(text='''Hello!
        Welcome to aMAZEing!
        You are this sphere,
        and your goal is to find the exit of the maze! Each level
        of the maze has a hole you can drop through, to move on to the
        next level. This maze has six levels and each maze is a 12x12.
        If you chose timer mode, you have 5 minutes to finish the maze,
        or else you lose.
        Good luck! You're aMAZEing :)''', style = 1, 
                fg=(0, 0, 0, 1), pos=(0, -.1), align=TextNode.ACenter, scale=0.07)
        self.instr.append(inst10)

    def deleteInstructions(self):
        #deletes onscreen instructions
        for instr in self.instr:
            instr.destroy()

    def addNotification(self, txt):
        #adds a notification to the screen
        y = 0.9
        tex = OnscreenText(text=txt, style=1, fg= (0, 0, 0, 1), pos=(0, y))
        self.messages.append(tex)

    def deleteNotifications(self):
        #deletes all on-screen notifications
        for msg in self.messages:
            msg.destroy()

    def updateLevelText(self):
        #updates the level text
        self.levelText.destroy()

        levelTextPos = (-1.3, -0.95)
        levelScale = 0.07

        self.levelText = OnscreenText(text= "Level = " + str(self.level), 
                style=1, fg=(0, 0, 0, 1), pos=levelTextPos, 
                align=TextNode.ALeft, scale=levelScale)

    def updateDirectionText(self):
        #updates the direction text on the screen
        self.directionText.destroy()

        directionTextPos = (-1.3, -0.85)
        directionScale = 0.07

        self.directionText = OnscreenText(text="Direction = " + self.direction,
                style=1, fg=(0, 0, 0, 1), pos=directionTextPos,
                align=TextNode.ALeft, scale=directionScale)

    def updateTimerText(self):
        #updates timer on screen
        self.timerText.destroy()

        timerTextPos = (1.3, 0.85)
        timerScale = 0.07

        if self.mode == "timer":
            self.timerText = OnscreenText(text= self.timer, 
                style=1, fg=(1, 1, 1, 1), pos=timerTextPos, 
                align=TextNode.ARight, scale=timerScale)

    def turnWallNotification(self):
        #give a notification sequence at the beginning
        notificationSeq = Sequence()
        notificationSeq.append(Func(addNotification,"""
        If you just see a blank color,
        it means you are facing a wall :)"""))
        notificationSeq.append(Wait(8))
        notificationSeq.append(Func(deleteNotifications))
        notificationSeq.start()

    def promptMode(self):
        #prompts for the mode
        modeScreen = SplashScreen()
        modeScreen.mode()

    def setMode(self, mode):
        #sets the mode of the game
        self.mode = mode
        
        if self.mode == "timer":
            self.setTimer()

    ###################### Initialization Helper Functions #####################

    def createBackground(self):
        #black feautureless space
        base.win.setClearColor(Vec4(0,0,0,1))

    def loadWallModel(self):
        #loads the wall model (the maze) 
        wallScale = 0.3
        wallModelName = self.randomWallModel()
            #randomly select a maze

        self.wallModel = loader.loadModel(wallModelName)
        self.wallModel.setScale(wallScale)
        self.wallModel.setPos(0, 0, 0)
        self.wallModel.setCollideMask(BitMask32.allOff())
        self.wallModel.reparentTo(render)

        ### Setting Texture ###
        texScale = 0.08
        self.wallModel.setTexGen(TextureStage.getDefault(),
                                   TexGenAttrib.MWorldNormal)
        self.wallModel.setTexProjector(TextureStage.getDefault(),
                                         render, self.wallModel)
        self.wallModel.setTexScale(TextureStage.getDefault(), texScale)
        tex = loader.load3DTexture('/Users/jianwei/Documents/School/Freshman/Semester1/15-112/TERMPROJECT/Project/wallTex/wallTex_#.png')
        self.wallModel.setTexture(tex)

        #creating visual geometry collision
        self.wallModel.setCollideMask(BitMask32.bit(0))

    def randomWallModel(self):
        #generates a random wall in the library of mazes that were 
        #randomly generated by the Blender script "mazeGenerator"
        #and exported to this computer
        numMazes = 10

        name = str(random.randint(0, numMazes))
            #randomly selects a number saved in the computer

        path = "/Users/jianwei/Documents/School/Freshman/Semester1/15-112/TERMPROJECT/Project/mazeModels/maze"

        path += name 

        return path
        
    def loadBallModel(self):
        #loads the character, a ball model

        #ballModelStartPos = (-8, -8, 0.701) #THIS IS THE END
        ballModelStartPos = (8, 8, 13.301) #level 0 
        ballScale = 0.01
        self.ballModel = loader.loadModel("/Users/jianwei/Documents/School/Freshman/Semester1/15-112/TERMPROJECT/Project/ball")
        self.ballModel.reparentTo(render)
        self.ballModel.setScale(ballScale)
        self.ballModel.setPos(ballModelStartPos)


        ### Setting ball texture ###
        texScale = 0.08
        self.ballModel.setTexGen(TextureStage.getDefault(),
                                   TexGenAttrib.MWorldPosition)
        self.ballModel.setTexProjector(TextureStage.getDefault(), 
                                         render, self.ballModel)
        self.ballModel.setTexScale(TextureStage.getDefault(), texScale)
        tex = loader.load3DTexture('/Users/jianwei/Documents/School/Freshman/Semester1/15-112/TERMPROJECT/Project/ballTex/ballTex_#.png')
        self.ballModel.setTexture(tex)

    def setCamera(self):
        #sets up the initial camera location
        #camera will follow the sphere 
        followLength = 2
        camHeight = 0.2

        base.disableMouse()
        base.camera.setPos(self.ballModel.getX(),
                                self.ballModel.getY() - followLength,
                                self.ballModel.getZ() + camHeight)
        base.camLens.setNear(0.4)

        #creates a floater object - will look at the floater object 
        #above the sphere, so you can get a better view
        self.floater = NodePath(PandaNode("floater"))
        self.floater.reparentTo(render)

    def createKeyControls(self):
        #creates the controllers for the keys
        #event handler
        #describes what each key does when pressed and unpressed

        self.accept("escape", sys.exit)

        self.accept("arrow_left", self.turnLeft)
        self.accept("arrow_right", self.turnRight)
        self.accept("arrow_up", self.setKey, ["forward",1])
        self.accept("arrow_down", self.setKey, ["backward",1])
        self.accept("space", self.nowDropping)

        #unpressed event handlers
        self.accept("arrow_left-up", self.setKey, ["left",0])
        self.accept("arrow_right-up", self.setKey, ["right",0])
        self.accept("arrow_up-up", self.setKey, ["forward",0])
        self.accept("arrow_down-up", self.setKey, ["backward",0])
        self.accept("space_up", self.setKey, ["drop", 0])

        #views
        self.accept('x', self.toggle_xray_mode)
        self.accept('c', self.toggle_collision_mode)
        self.accept('z', self.toggle_wireframe)

        #information
        self.accept('i', self.postInstructions)
        self.accept('i-up', self.deleteInstructions)

        #restart
        self.accept('r', self.restart)

        #modes
        self.accept("t", self.setMode, ["timer"])
        self.accept("m", self.setMode, ["marathon"])

    def createBallColliderModel(self):
        #creates the collider sphere around the ball
        cSphereRad = 9.9
        self.cTrav = CollisionTraverser() #moves over all possible collisions

        self.ballModelSphere = CollisionSphere(0, 0, 0, cSphereRad)
            #collision mesh around ball is a simple sphere
        self.ballModelCol = CollisionNode('ballModelSphere')
        self.ballModelCol.addSolid(self.ballModelSphere)
        self.ballModelCol.setFromCollideMask(BitMask32.bit(0))
        self.ballModelCol.setIntoCollideMask(BitMask32.allOff())
        self.ballModelColNp = self.ballModel.attachNewNode(self.ballModelCol)
        self.ballModelGroundHandler = CollisionHandlerQueue()
            #collision handler queue stores all collision points
        self.cTrav.addCollider(self.ballModelColNp, self.ballModelGroundHandler)

    def createLighting(self):
        #creates lighting for the scene
        aLightVal = 0.3
        dLightVal1 = -5
        dLightVal2 = 5

        #set up the ambient light
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor(Vec4(aLightVal, aLightVal, aLightVal, 1))
        ambientLight1 = AmbientLight("ambientLight1")
        ambientLight1.setColor(Vec4(aLightVal, aLightVal, aLightVal, 1))
        ambientLight2 = AmbientLight("ambientLight2")
        ambientLight2.setColor(Vec4(aLightVal, aLightVal, aLightVal, 1))

        #sets a directional light
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(Vec3(dLightVal1, dLightVal1, dLightVal1))
        directionalLight.setColor(Vec4(1, 1, 1, 1))
        directionalLight.setSpecularColor(Vec4(0, 0, 0, 1))

        #sets a directional light
        directionalLight1 = DirectionalLight("directionalLight2")
        directionalLight1.setDirection(Vec3(dLightVal2, dLightVal1, dLightVal1))
        directionalLight1.setColor(Vec4(1, 1, 1, 1))
        directionalLight1.setSpecularColor(Vec4(1, 1, 1, 1))


        #attaches lights to scene
        render.setLight(render.attachNewNode(ambientLight))
        render.setLight(render.attachNewNode(ambientLight1))
        render.setLight(render.attachNewNode(ambientLight1))
        render.setLight(render.attachNewNode(directionalLight))
        render.setLight(render.attachNewNode(directionalLight1))

###################### COLLISION DETECTION #####################################

    def traverseTask(self, task=None):
        # handles collisions with collision handers and a 
        # collision queue
        # essentially checks region of potential collision for collisions
        # and stops the ball if a collision is triggered
        # called by task manager
        self.ballModelGroundHandler.sortEntries()
        for i in range(self.ballModelGroundHandler.getNumEntries()):
            entry = self.ballModelGroundHandler.getEntry(i)

            if self.drop == True:
                #we cant drop in this situation
                self.ballModel.setZ(self.currentHeight)

                dropFailWait = 4
                dropFailSeq = Sequence()
                dropFailSeq.append(Func(addNotification,"Whoops! You can't drop here!"))
                dropFailSeq.append(Wait(dropFailWait))
                dropFailSeq.append(Func(deleteNotifications))
                dropFailSeq.start()

                self.drop = False

            elif self.direction == "N":
                self.northDisableMovements()

            elif self.direction == "S":
                self.southDisableMovements()

            elif self.direction == "E":
                self.eastDisableMovements()

            elif self.direction == "W":
                self.westDisableMovements()

            if task: return task.cont #exit task

        # If there are no collisions
        
        if task: return task.cont

    def northDisableMovements(self):
        #disables movements when direction is north
        if self.keyMap["forward"] != 0: #if the ball was moving foward
            self.disableForwardMovement = True #disable forward movement
        if self.keyMap["backward"] != 0:
            self.disableBackwardMovement = True

    def southDisableMovements(self):
        #disables movements when direction is south
        if self.keyMap["forward"] != 0: 
            self.disableBackwardMovement = True 
        if self.keyMap["backward"] != 0:
            self.disableForwardMovement = True

    def eastDisableMovements(self):
        #disables movements when direction is east
        if self.keyMap["forward"] != 0: 
            self.disableRightMovement = True 
        if self.keyMap["backward"] != 0:
            self.disableLeftMovement = True

    def westDisableMovements(self):
        #disables movements when direction is west
        if self.keyMap["forward"] != 0: 
            self.disableLeftMovement = True 
        if self.keyMap["backward"] != 0:
            self.disableRightMovement = True

    def checkCollisions(self):
        #checks for collisions
        self.cTrav.traverse(render)

    def enableAllWalls(self):
        #enables all walls by disabling all the disable wall functions
        self.disableLeftMovement = False
        self.disableRightMovement = False 
        self.disableForwardMovement = False
        self.disableBackwardMovement = False

    def inCollision(self):
        #return true if we are in a collision right now, false otherwise
        if (self.disableForwardMovement == True
            or self.disableBackwardMovement == True 
            or self.disableRightMovement == True 
            or self.disableLeftMovement):
            return True
        return False

    def checkForWin(self):
        #checks for a win, toggles win splash sceen if we win
        yLoc = self.ballModel.getY()
        exitBound = -9.1

        if yLoc < exitBound: 
            winScreen = SplashScreen()
            winScreen.win()

        if self.mode == "timer":
            self.checkForTimerLoss()

    def checkForTimerLoss(self):
        #checks to see the time, will lose if past 5 minutes
        
        if self.timer == "0:05:00":
            loseScreen = SplashScreen()
            loseScreen.lose()

###################### MOVEMENTS ###############################################

    def move(self, task):
        # Accepts arrow keys to move the player front and back
        # Also deals with grid checking and collision detection

        step = 0.03

        #movement animation
        self.movementAnimation(step)
        #rotation animation
        self.rotationAnimation()

        base.camera.setX(self.ballModel.getX() + math.sin(self.camAngle))
        base.camera.setY(self.ballModel.getY() + math.cos(self.camAngle))

        self.resetCamDist()
        self.checkCollisions()
        self.lookAtFloater()

        self.checkForWin()

        return task.cont

    def resetCamDist(self):
        #resets the camera distance to a specific distance
        #keeps distance relatively constant
        camFarDist = 0.75
        camCloseDist = 0.7

        camvec = self.ballModel.getPos() - base.camera.getPos()
            #vector between ball and camera
        camvec.setZ(0)
        camdist = camvec.length()
        camvec.normalize()

        if (camdist > camFarDist):
            base.camera.setPos(base.camera.getPos() + 
                                    camvec*(camdist-camFarDist))
            camdist = camFarDist

        if (camdist < camCloseDist):
            base.camera.setPos(base.camera.getPos() -
                                    camvec*(camCloseDist-camdist))
            camdist = camCloseDist

        base.camera.lookAt(self.ballModel)

    def lookAtFloater(self):
        #looks at the floater above the sphere
        floaterHeight = 0.23
        self.floater.setPos(self.ballModel.getPos())
        self.floater.setZ(self.ballModel.getZ() + floaterHeight)
        base.camera.lookAt(self.floater)

    ####################### Movement Animation #################################

    def ballIsMoving(self):
        #notes if the ball is moving or not with self.isMoving variable
        if (self.keyMap["forward"]!=0) or (self.keyMap["backward"]!=0):
            if self.isMoving == False:
                self.isMoving = True

        elif self.keyMap["forward"] == 0 and self.keyMap["backward"] == 0:
            self.isMoving = False

    def movementAnimation(self, step):
        #describes the movement animation
        if self.drop == True:
            self.dropMovementAnimation(step)
        elif self.direction == "N":
            self.northMovementAnimation(step)

        elif self.direction == "S":
            self.southMovementAnimation(step)

        elif self.direction == "E":
            self.eastMovementAnimation(step)

        elif self.direction == "W":
            self.westMovementAnimation(step)

    def northMovementAnimation(self, step):
        #describes animation when direction is north
        if (self.keyMap["forward"]!=0):
            #if you are pressing forward
            if self.disableForwardMovement == False:
                #if you are just moving through space...
                self.ballModel.setY(self.ballModel.getY() + step)
            if self.disableBackwardMovement == True:
                #if you had moved backwards into a wall
                #and you want to move forward again
                self.ballModel.setY(self.ballModel.getY() + step)
                self.disableBackwardMovement = False
                

        if (self.keyMap["backward"]!=0):
            #if you are pressing backwards
            if self.disableBackwardMovement == False:
                #if you are just moving backwards through space...
                self.ballModel.setY(self.ballModel.getY() - step)
            if self.disableForwardMovement == True:
                #if you had moved forward into a wall
                #and want to back away from the wall
                self.ballModel.setY(self.ballModel.getY() - step)
                self.disableForwardMovement = False        

    def southMovementAnimation(self, step):
        #describes animation when direction is north
        #same relative set of animations to northMovementAnimation
        #but opposite
        if (self.keyMap["forward"]!=0):
            if self.disableBackwardMovement == False:
                self.ballModel.setY(self.ballModel.getY() - step)
            if self.disableForwardMovement == True:
                self.ballModel.setY(self.ballModel.getY() - step)
                self.disableForwardMovement = False

        if (self.keyMap["backward"]!=0):
            if self.disableForwardMovement == False:
                self.ballModel.setY(self.ballModel.getY() + step)
            if self.disableBackwardMovement == True:
                self.ballModel.setY(self.ballModel.getY() + step)
                self.disableBackwardMovement = False        

    def eastMovementAnimation(self, step):
        #describes animation when direction is east
        #same relative as north and south movement animations
        #but relative to the x axis
        #and disabling/enabling right and left movement at collisions
        if (self.keyMap["forward"]!=0):
            if self.disableRightMovement == False:
                self.ballModel.setX(self.ballModel.getX() + step)
            if self.disableLeftMovement == True:
                self.ballModel.setX(self.ballModel.getX() + step)
                self.disableLeftMovement = False

        if (self.keyMap["backward"]!=0):
            if self.disableLeftMovement == False:
                self.ballModel.setX(self.ballModel.getX() - step)
            if self.disableRightMovement == True:
                self.ballModel.setX(self.ballModel.getX() - step)
                self.disableRightMovement = False

    def westMovementAnimation(self, step):
        #describes animation when direction is west
        #relatively same animations as the east movement animations
        #exact opposite
        if (self.keyMap["forward"]!=0):
            if self.disableLeftMovement == False:
                self.ballModel.setX(self.ballModel.getX() - step)
            if self.disableRightMovement == True:
                self.ballModel.setX(self.ballModel.getX() - step)
                self.disableRightMovement = False

        if (self.keyMap["backward"]!=0):
            if self.disableRightMovement == False:
                self.ballModel.setX(self.ballModel.getX() + step)
            if self.disableLeftMovement == True:
                self.ballModel.setX(self.ballModel.getX() + step)
                self.disableLeftMovement = False

    def turnRight(self):
        #turns right in the animation

        #uses an interval to slowly rotate camera around
        initial = self.camAngle
        final = self.camAngle + math.pi/2

        #turn animation
        turnTime = 0.2
        turnRightSeq = Sequence()
        turnRightSeq.append(LerpFunc(self.changeCamAngle, turnTime, initial,
                                                         final, 'easeInOut'))
        turnRightSeq.start()

        self.setKey("right", 1) #notes that the right key is pressed

        #changes the direction right, based on current direction
        if self.direction == "N":
            self.direction = "E"
        elif self.direction == "E":
            self.direction = "S"
        elif self.direction == "S":
            self.direction = "W"
        else:
            self.direction = "N"

        #when you turn, all the collision disablements should be True
        #just checking
        #self.enableAllWalls()

        #update the label
        self.updateDirectionText()

    def turnLeft(self):
        #turns left

        initial = self.camAngle
        final = self.camAngle - math.pi/2

        #turn animation
        turnTime = 0.2
        turnRightSeq = Sequence()
        turnRightSeq.append(LerpFunc(self.changeCamAngle, turnTime, initial,
                                                         final, 'easeInOut'))
        turnRightSeq.start()


        self.setKey("left", 1) #notes that left key is pressed

        #changes the direction left, based on current direction
        if self.direction == "N":
            self.direction = "W"
        elif self.direction == "W":
            self.direction = "S"
        elif self.direction == "S":
            self.direction = "E"
        else:
            self.direction = "N"

        #when you turn, all the collision disablements should be True
        #just checking
        #self.enableAllWalls()

        #update the label
        self.updateDirectionText()

    def changeCamAngle(self, angle):
        #changes the camAngle to angle
        self.camAngle = angle

    def dropMovementAnimation(self, step):
        #describes movement when drop is hit

        a = 0.1

        if self.keyMap["drop"] != 0:
            if self.ballModel.getZ() > self.currentHeight - self.levelHeight+ a:
                self.ballModel.setZ(self.ballModel.getZ() - step)
            else:
                self.currentHeight -= self.levelHeight
                self.level += 1
                self.updateLevelText()
                self.drop = False
                base.camera.setZ(self.ballModel.getZ() + self.cameraHeight)

    def nowDropping(self):
        #toggles isDropping boolean
        self.drop = True
        self.setKey("drop", 1)
        
    ################## Ball Rotation Animation #################################

    def rotationAnimation(self):
        #describes the rotation movement of sphere
        self.ballIsMoving()
        speed=300
        inCollision = self.inCollision()

        if self.isMoving and not inCollision:
            if self.direction == "N":
                self.northRotationAnimation(speed)
            if self.direction == "S":
                self.southRotationAnimation(speed)
            if self.direction == "E":
                self.eastRotationAnimation(speed)
            if self.direction == "W":
                self.westRotationAnimation(speed)

    def northRotationAnimation(self, speed):
        #describes the rotation animation if direction is north
        if self.keyMap["forward"] != 0:
            self.ballModel.setP(self.ballModel.getP()-speed*globalClock.getDt())
        elif self.keyMap["backward"] != 0:
            self.ballModel.setP(self.ballModel.getP()+speed*globalClock.getDt())

    def southRotationAnimation(self, speed):
        #describes the rotaiton animation if the direction is south
        if self.keyMap["backward"] != 0:
            self.ballModel.setP(self.ballModel.getP()-speed*globalClock.getDt())
        elif self.keyMap["forward"] != 0:
            self.ballModel.setP(self.ballModel.getP()+speed*globalClock.getDt())

    def eastRotationAnimation(self, speed):
        #describes the rotation animation if the direction is east
        if self.keyMap["backward"] != 0:
            self.ballModel.setR(self.ballModel.getR()-speed*globalClock.getDt())
        elif self.keyMap["forward"] != 0:
            self.ballModel.setR(self.ballModel.getR()+speed*globalClock.getDt())

    def westRotationAnimation(self, speed):
        #describes the rotation animation if the direction is west
        if self.keyMap["forward"] != 0:
            self.ballModel.setR(self.ballModel.getR()-speed*globalClock.getDt())
        elif self.keyMap["backward"] != 0:
            self.ballModel.setR(self.ballModel.getR()+speed*globalClock.getDt())

###################### VIEWS ###################################################

    def toggle_xray_mode(self):
        #Toggle X-ray mode on and off.
        #Note: slows down program considerably
        xRayA = 0.5
        self.xray_mode = not self.xray_mode
        if self.xray_mode:
            self.wallModel.setColorScale((1, 1, 1, xRayA))
            self.wallModel.setTransparency(TransparencyAttrib.MDual)
        else:
            self.wallModel.setColorScaleOff()
            self.wallModel.setTransparency(TransparencyAttrib.MNone)

    def toggle_collision_mode(self):
        #Toggle collision mode on and off
        #Shows visual representation of the collisions occuring
        self.collision_mode = not self.collision_mode
        if self.collision_mode == True:
            # Note: Slows the program down considerably
            self.cTrav.showCollisions(render)
        else:
            self.cTrav.hideCollisions()

    def toggle_wireframe(self):
        #toggles wireframe view
        self.wireframe = not self.wireframe
        if self.wireframe:
            self.wallModel.setRenderModeWireframe()
        else:
            self.wallModel.setRenderModeFilled()

##################### RESTART ##################################################
    
    def restart(self):
        #restarts the game
        loading = SplashScreen()
        loading.loading()
        self.reset()

    def reset(self):
        #resets the maze, resets the location of the character

        #removes all notes
        self.wallModel.removeNode()
        self.ballModel.removeNode()

        #resets notes
        self.loadWallModel()
        self.loadBallModel()
        self.createBallColliderModel()
        self.resetCamDist()

        #resets timers
        taskMgr.remove("timerTask")
        self.timer = ""
        self.timerText.destroy()

        self.promptMode()

#################### TIMER #####################################################

    def setTimer(self):
        #code from panda.egg user on Panda3D, 
        #"How to use Timer, a small example maybe?" forum
        #creates a timer
        self.timer = DirectLabel(pos=Vec3(1, 0.85),scale=0.08)

        taskMgr.add(self.timerTask, "timerTask")

    def dCharstr(self, theString):
        #code from panda.egg user on Panda3D, 
        #"How to use Timer, a small example maybe?" forum
        #turns time string into a readable clock string
        if len(theString) != 2:
            theString = '0' + theString
        return theString

    def timerTask(self, task):
        #code from panda.egg user on Panda3D, 
        #"How to use Timer, a small example maybe?" forum
        #task for resetting timer in timer mode
        secondsTime = int(task.time)
        minutesTime = int(secondsTime/60)
        hoursTime = int(minutesTime/60)
        self.timer = (str(hoursTime) + ':' 
                            + self.dCharstr(str(minutesTime%60)) + ':' 
                            + self.dCharstr(str(secondsTime%60)))

        self.updateTimerText()
        
        return Task.cont


def playGame():
    #plays the maze game!
    w = World()
    base.run()

playGame()

