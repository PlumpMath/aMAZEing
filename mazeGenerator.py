# MazeGenerator- Jessie Li
# December 8, 2015
# With Code from David Kosbie 15-112 Class Notes
# And adapted from Ella Jameson, from Thingiverse, published March, 24, 2015

# This is a python script, which the application Blender uses to create a 
# three dimensional maze, made of of two dimensional maze layers.
# The Blender mazes must then be manually exported (through the Blender Render 
# engine) in a .egg format and will then be projected and run through the 
# program Panda3D.

import random
import bpy

def deletePresentObjects():
    #deletes the objects already present in the scene
    #Code directly from Ella Jameson
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()

def make2dList(rows, cols):
    #David Kosbie, 15-112 Carnegie Mellon University Course Notes
    #makes an empty 2d list, initializing each original cell to False
    a=[]
    for row in range(rows): a += [[False]*cols]
    return a

class Maze(object):
    #the class of Mazes
    #with code adapted from Ella Jameson

    def __init__(self, level, entrance=False, exit=False, base=True):
        #constructor for Maze object

        ##### Maze Dimensions #####
        self.width = 12                  #how many cells wide
        self.length = 12                 #how many cells long
        self.cellWidth = 4               #width of passages [mm](cell thickness)
        self.wallWidth = 1               #width of walls [mm]   (wall thickness)
        self.wallHeight = 5              #height of walls [mm] (0 = flat path)
        self.baseHeight = 2              #height of base [mm] (0 = no base)

        ##### Maze Structure #####
        self.level = level
        self.entrance = entrance
        self.exit = exit
        self.base = base

        ##### Maze Generation Variables #####
        self.directions = ["n", "s", "e", "w"]
        self.stack = [] #to keep track of the branches, psuedo-recursively

        self.currentCell = [self.width - 1, self.length - 1] 
            #start at the end of the maze, makes exit dead end
        self.explored = make2dList(self.width, self.length)
            #list of cells that have been explored (list of booleans)

        self.mesh = None  #mesh of the maze that will be created 

        self.z = self.baseHeight*self.level + self.wallHeight*self.level 
            #height of the level of the maze

        ##### Maze Generation #####
        self.verts = [] #list of all the vertices of walls (2D plane)
        self.initializeVertices()
        self.faces = [] #list of the tuples of vertices that make a wall
        self.initializeFaces()

        self.facesToDelete = [False for n in range(0, len(self.faces))]
            #1D list of faces that need to be deleted at the end (1D)

        self.createMaze()
        self.createEntrancesAndExits()
        self.deleteFaces()
        self.createMesh()

    def initializeVertices(self):
        #initializes the array of vertices used to represent each cell 
        #each c represents a different corner of a cell
        #takes into account wall size
        #variable c is just used for finding index of vertex in list
        unitWidth = self.wallWidth + self.cellWidth

        #c = 0 (bottom left) squares grid
        for y in range(0, self.length + 1):
            for x in range(0, self.width + 1):
                vertex = (unitWidth*x, unitWidth*y, 0)
                self.verts.append(vertex)

        #c = 1 (bottom right) squares grid
        for y in range(0, self.length + 1):
            for x in range(0, self.width + 1):
                vertex = (unitWidth*x + self.wallWidth, unitWidth*y, 0)
                self.verts.append(vertex)

        #c = 2 (top left) squares grid
        for y in range(0, self.length + 1):
            for x in range(0, self.width + 1):
                vertex = (unitWidth*x, unitWidth*y + self.wallWidth, 0)
                self.verts.append(vertex)

        #c = 3 (top right) squares grid
        for y in range(0, self.length + 1):
            for x in range(0, self.width + 1):
                vertex = (unitWidth*x + self.wallWidth, 
                                        unitWidth*y + self.wallWidth, 0)
                self.verts.append(vertex)

    def vertIndex(self, x, y, c):
        #returns the index of (x,y) in self.verts
        return ((c * ((self.length + 1) * (self.width + 1))) + 
                                                (((self.width + 1) * y) + x))

    def initializeFaces(self):
        #makes the initial list of faces (to draw in Blender)

        #first, the horizontals (of the walls)
        c0, c1, c2, c3 = 0, 1, 2, 3

        for y in range(0, self.length + 1):
            for x in range(0, self.width):
                self.faces.append((self.vertIndex(x, y, c1), 
                                        self.vertIndex(x + 1, y, c0), 
                                        self.vertIndex(x + 1, y, c2), 
                                        self.vertIndex(x, y, c3)))

        #then, the verticals (of the walls)
        for y in range(0, self.length):
            for x in range(0, self.width + 1):
                self.faces.append((self.vertIndex(x, y, c2), 
                                        self.vertIndex(x, y, c3), 
                                        self.vertIndex(x, y + 1, c1), 
                                        self.vertIndex(x, y + 1, c0)))

        #finally, the squares themselves
        for y in range(0, self.length + 1):
            for x in range(0, self.width + 1):
                self.faces.append((self.vertIndex(x, y, c0), 
                                        self.vertIndex(x, y, c1), 
                                        self.vertIndex(x, y, c3), 
                                        self.vertIndex(x, y, c2)))

    def canMove(self, dir):
        #tests legality of a move in maze generation

        if dir == "n":
            if self.currentCell[1] < self.length - 1: #y value not out of bounds
                if self.explored[self.currentCell[0]][self.currentCell[1] + 1]:
                    #if it has been explored...
                    return False
                else: return True
            else: return False
        
        elif dir == "s":
            if self.currentCell[1] > 0: #y value not out of bounds
                if self.explored[self.currentCell[0]][self.currentCell[1] - 1]:
                    return False
                else: return True
            else: return False
        
        elif dir == "e":
            if self.currentCell[0] < self.width - 1:
                if self.explored[self.currentCell[0] + 1][self.currentCell[1]]:
                    return False
                else: return True
            else: return False
        
        elif dir == "w":
            if self.currentCell[0] > 0:
                if self.explored[self.currentCell[0] - 1][self.currentCell[1]]:
                    return False
                else: return True
            else: return False

    def move(self, dir):
        #actually moving through the maze during generation
        if dir == "n":
            self.facesToDelete[(self.width * (self.currentCell[1] + 1)) 
                                            + self.currentCell[0]] = True
            #keeps track of which face of which cell to delete with a boolean
            self.currentCell[1] += 1 
            #moves the current cell in the specific direction
        elif dir == "s":
            self.facesToDelete[(self.width * self.currentCell[1]) 
                                            + self.currentCell[0]] = True
            self.currentCell[1] -= 1
        elif dir == "e":
            self.facesToDelete[(self.width * (self.length + 1)) + 
                            ((self.width + 1) * self.currentCell[1]) + 
                            self.currentCell[0] + 1] = True
            self.currentCell[0] += 1
        elif dir == "w":
            self.facesToDelete[(self.width * (self.length + 1)) + 
                                ((self.width + 1) * self.currentCell[1]) + 
                                    self.currentCell[0]] = True
            self.currentCell[0] -= 1

    def createMaze(self):
        #creates a maze
        while True:
        #keep running while maze needs to be solved

            #we've explored a new cell!
            self.explored[self.currentCell[0]][self.currentCell[1]] = True
            
            #randomize directions
            random.shuffle(self.directions)

            d0, d1, d2, d3 = 0, 1, 2, 3
            
            #tries every single move in randomized order
            if self.canMove(self.directions[d0]):
                self.stack.append(self.currentCell[:])
                self.move(self.directions[d0])
            elif self.canMove(self.directions[d1]):
                self.stack.append(self.currentCell[:])
                self.move(self.directions[d1])
            elif self.canMove(self.directions[d2]):
                self.stack.append(self.currentCell[:])
                self.move(self.directions[d2])
            elif self.canMove(self.directions[d3]):
                self.stack.append(self.currentCell[:])
                self.move(self.directions[d3])
            else: #if no direction can be moved into
                self.currentCell = self.stack.pop()
                
            #finally, check if stack is empty
            #maze will be created if the stack is completely empty
            #no more possible movements
            if (len(self.stack) == 0):
                break

    def createEntrancesAndExits(self):
        #make an entrance to the size of the 2D maze
        if self.entrance == True:
            self.facesToDelete[0] = True 
            #deletes first face
        if self.exit == True:
            #creates an exit
            self.facesToDelete[((self.length + 1) * self.width) - 1] = True
            #deletes last face
            #need to selectively randomize doors 

    def deleteFaces(self):
        #last vert/face operation, delete the faces marked for deleteing
        for n in range(len(self.faces), 0, -1):
            if self.facesToDelete[n - 1]:
                self.faces.pop(n - 1)

    def createMesh(self):
        #creates the mesh of the maze (for Blender)
        mazeMesh = bpy.data.meshes.new("MazeMesh") #create a new mesh  

        #fill the mesh with verts, edges, faces 
        mazeMesh.from_pydata(self.verts,[],self.faces)
        mazeMesh.update(calc_edges=True)    #update mesh with new data

        self.mesh = mazeMesh

    def createMazeObject(self):
        #creates the maze object (in Blender when script is run)

        mazeObj = bpy.data.objects.new(str(self.level), self.mesh) 
                    #create an object with your mesh, name is level name
        mazeObj.location = (0, 0, self.z) 
                    #position object at the center, at its level height
        bpy.context.scene.objects.link(mazeObj) #link object to scene

        #extrusion
        bpy.context.scene.objects.active = bpy.data.objects[str(self.level)] 
            #set as active
        bpy.ops.object.editmode_toggle()
        ############################# EDIT MODE ################################

        #extrude to wallHeight
        bpy.ops.mesh.extrude_region_move(
            MESH_OT_extrude_region={"mirror":False}, 
            TRANSFORM_OT_translate={"value":(0, 0, self.wallHeight), 
            "constraint_axis":(False, False, True), 
            "constraint_orientation":'NORMAL', "mirror":False, 
            "proportional":'DISABLED', "proportional_edit_falloff":'SMOOTH', 
            "proportional_size":1, "snap":False, "snap_target":'CLOSEST', 
            "snap_point":(0, 0, 0), "snap_align":False, "snap_normal":(0, 0, 0), 
            "texture_space":False, "remove_on_cancel":False, 
            "release_confirm":False})

        #fix normals
        bpy.ops.mesh.normals_make_consistent(inside=False)

        bpy.ops.object.editmode_toggle() #object mode now
        ########################### OBJECT MODE ################################

        bpy.ops.object.select_pattern(pattern=str(self.level)) #select

        self.addBase()

        # simplify final mesh
        bpy.ops.object.editmode_toggle() #edit mode now
        bpy.ops.object.select_pattern(pattern=str(self.level))
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.mesh.dissolve_limited()
        bpy.ops.object.editmode_toggle() #object mode now

        #center it
        bpy.ops.object.select_pattern(pattern=str(self.level))
        bpy.context.scene.cursor_location = [((self.width * self.cellWidth) + 
            ((self.width + 1) * self.wallWidth)) / 2, 
        ((self.length * self.cellWidth) + 
            ((self.length + 1) * self.wallWidth)) / 2, self.z]
        bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
        bpy.context.object.location = [0, 0, self.z]
        bpy.context.scene.cursor_location = [0, 0, self.z]
            
        bpy.ops.object.select_all(action='DESELECT') #deselect all objects

    def addBase(self):
        #adds the base to the blender scene, joins objects
        bRadius = 0.5
        bpy.context.object.location[2] += self.baseHeight #move up
        
        #add the base cube

        #dimensions of the base of the cube
        x = self.width*self.cellWidth + (self.width + 1)*self.wallWidth
        y = self.length*self.cellWidth + (self.length + 1)*self.wallWidth
        z = self.baseHeight
        bpy.ops.mesh.primitive_cube_add(radius = bRadius, 
            location=(x/2, y/2, z/2 + self.z)) #make cube, move location
        bpy.ops.transform.resize(value=(((self.width * self.cellWidth) + 
            ((self.width + 1) * self.wallWidth)), 
        ((self.length * self.cellWidth) + 
            ((self.length + 1) * self.wallWidth)), self.baseHeight))

        for obj in bpy.context.selected_objects:
            obj.name = "Base" #name object Base

        bpy.ops.object.select_all(action='DESELECT')

        if self.base: #creates base hole (if needed)
            self.createBaseHole()

        #joining base and mase together (by adding a union modifier)
        bpy.context.scene.objects.active = bpy.data.objects[str(self.level)] 
            #set as active
        bpy.ops.object.modifier_add(type='BOOLEAN')
        bpy.context.object.modifiers["Boolean"].operation = 'UNION'
        bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["Base"]
        bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")
        bpy.ops.object.select_pattern(pattern="Base")
        bpy.ops.object.delete(use_global=False)

    def createBaseHole(self):
        #creates the hole in the base of the maze
        holeSubtract = 2.3

        #compute a random location in maze
        xIndex = random.randint(0, self.width-1)
        yIndex = random.randint(0, self.length-1)
        xLeft =  max(0, self.wallWidth*xIndex + self.cellWidth*(xIndex-1))
        xRight = min(xLeft + self.cellWidth, self.width*self.cellWidth + 
                            (self.width + 1)*self.wallWidth)
        yBottom = max(self.wallWidth*yIndex + self.cellWidth*(yIndex-1), 0)
        yTop = min(yBottom + self.cellWidth, self.length*self.cellWidth + 
                                        (self.length + 1)*self.wallWidth)

        #center the random location
        cx = (xRight+xLeft)/2
        cy = (yTop+yBottom)/2
        
        #create a cube in randomly generated location
        bpy.ops.mesh.primitive_cube_add(
                            location=(cx, cy, self.baseHeight/2+self.z))
        bpy.ops.transform.resize(
                        value=(self.cellWidth-holeSubtract*self.wallWidth, 
                        self.cellWidth-holeSubtract*self.wallWidth, 10))
 

        #name the cube "Cut"
        for obj in bpy.context.selected_objects:
            obj.name = "Cut"

        #your resulting object is now the difference between the two objects
        bpy.context.scene.objects.active = bpy.data.objects["Base"]
        bpy.ops.object.modifier_add(type="BOOLEAN")
        bpy.context.object.modifiers["Boolean"].operation = "DIFFERENCE"
        bpy.context.object.modifiers["Boolean"].object = bpy.data.objects["Cut"]

    def makeLid(self):
        #makes the top base of the maze
        bRadius = 0.5
        bpy.ops.mesh.primitive_cube_add(radius = bRadius, 
            location=(0, 0, self.baseHeight + self.z + self.wallHeight))
        bpy.ops.transform.resize(value=(((self.width * self.cellWidth) + 
            ((self.width + 1) * self.wallWidth)), 
        ((self.length * self.cellWidth) + 
            ((self.length + 1) * self.wallWidth)), self.baseHeight))
    

def joinMazes():
    #joins the seperate layers of 2D mazes into a single 3D layer
    for ob in bpy.context.scene.objects:
        ob.select = True
        bpy.context.scene.objects.active = ob
    bpy.ops.object.join()

def create3DMaze():
    #creates a 3D maze
    numLayers = 1 #number of layers wanted

    deletePresentObjects() #delete present objects in scene

    for i in range(numLayers):
        #creates each layer of the maze seperately
        base = True
        if i == 0: 
            entrance = True
            exit = False
            base = False
        elif i == numLayers - 1:
            entrance = False
            exit = False
        else:
            entrance = False
            exit = False

        myMaze = Maze(i, entrance, exit, base)
        #creates a maze representation
        myMaze.createMazeObject()
        #creates maze for processingi n Blender

        #if i == numLayers - 1: myMaze.makeLid()
        #adds a lid

    joinMazes() #joins all seperate parts of the maze into 1 object

create3DMaze()













