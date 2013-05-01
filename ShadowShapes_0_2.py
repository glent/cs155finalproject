# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Shadow Sketch Alpha",
    "author": "Peter Andrien, Gary Lent",
    "version": (0,1),
    "blender": (2, 5, 9),
    "api": 39307,
    "location": "View3D > Tools > Parameteriz Object",
    "description": "Creates Meshes Using Silhouette, based on the 2010 sigraph paper.",
    "warning": "",
    "wiki_url": "",
    "tracker_url": "",
    "category": "Mesh"}

import bpy
from mathutils import Vector
from copy import deepcopy
#from math import abs

#Debug Line
from time import ctime
print("-------------------",ctime(),"-------------------")

ERROR_T = 0.000001

# ---- Properties ----
def setProp(propName, data, object=None):
    "Changes or Adds Property with data"
    if not object:
        object = bpy.context.object
    object[propName] = data


def hasProp(propName, object=None):
    "Return True iff object has property"
    if not object:
        object = bpy.context.object
    try:
        object[propName]
        return True
    except:
        return False


def getProp(propName, object=None):
    "Returns property if it exists"
    if not object:
        object = bpy.context.object
    try:
        return object[propName]
    except:
        #print("Error: Cannot Return Property Value")
        #print("Requested Property (" + propName + " does not exist")
        return False

def sortProp(propName,keyFunc):
    "Sort property using the given key"
    list = eval(getProp(propName))
    list.sort(key=keyFunc)
    setProp(propName,str(list))


def addEnum(propName,enum,label):
    "Work around for declaring enumerations"
    exec("bpy.types.Object." + \
         propName + " = bpy.props.EnumProperty(items=enum,name = label)")


# ---- Objects ----
def hasObject(objectName):
    try:
        bpy.data.objects[objectName]
        return True
    except:
        return False


def getObject(objectName):
    try:
        return bpy.data.objects[objectName]
    except:
        return False

def remProp(propName, object=None):
    "If property exists, removes property and returns True"
    if not object:
        object = bpy.context.object
    try:
        del(object[propName])
        return True
    except:
        print('Error: Cannot Delete')
        print("Requested Property ( " + propName + " ) does not exist")
        return False

def selectObjectName(objectName):
    for ob in bpy.data.objects:
        if ob.name == objectName:
            ob.select = True
        else:
            ob.select = False

def getSelectedObjects():
    return [ob for ob in bpy.data.objects if ob.select]

def addMesh(name, verts, faces):
        if name:
            me = bpy.data.meshes.new(name+'Mesh')
            ob = bpy.data.objects.new(name, me)
            ob.location = Vector()
            
            scn = bpy.context.scene
            scn.objects.link(ob)
            scn.objects.active = ob
            ob.select = True
         
            me.from_pydata(verts, [], faces)
            
            me.update()
            
            return ob
        return False

#=== The User Interface ===
class Panel(bpy.types.Panel):
    bl_label = "Silhouette"
    bl_space_type = "VIEW_3D"
    bl_region_type = "TOOLS"

    @classmethod
    def poll(self, context):
        try:
            if bpy.context.object == None:
                return true
            return bpy.context.object.mode == "OBJECT"
        except:
            return False
        
    def draw(self,context):
        layout = self.layout
        
        row1 = layout.row()
        row1.operator("add.obj", text="Add Silhouette Object")
        
        if hasProp("Silhouette"):
            box = layout.box()
            box.label("Active Object Silhouette Properties")
            box.prop(context.object, "silhouetteX", text="X Axis (Front)")
            box.prop(context.object, "silhouetteY", text="Y Axis (Side)")
            box.prop(context.object, "silhouetteZ", text="Z Axis (Top)")
            box.operator("generate.obj", text="Generate")
            box.operator("cleanup.obj", text="Remove Mesh")



#=== Operators ===
class MESH_OT_AddSilhouetteObject(bpy.types.Operator):
    bl_idname = "add.obj"
    bl_label = "Add Silhouette Object"

    def execute(self, context):
        bpy.ops.object.add(type = 'EMPTY')
        setProp("Silhouette", True)
        return{'FINISHED'}
    
class MESH_OT_Remove(bpy.types.Operator):
    bl_idname = "cleanup.obj"
    bl_label = "Remove Mesh"
    
    def execute(self, context):
        ob = context.object
        name = ob.name
        ob.select = False
        selectObjectName(name+"Surface")
        bpy.ops.object.delete()
        ob.select = True
        return{'FINISHED'}

class MESH_OT_GenerateMesh(bpy.types.Operator):
    bl_idname = "generate.obj"
    bl_label = "Generate Mesh"

    def execute(self, context):
        #print("\n+++++++++++++++++",ctime(),"+++++++++++++++++")
        
        #Get Generator Object
        ob = context.object
        name = ob.name
        loc = ob.location
        
        #Deleate Old Surface if it exists
        ob.select = False
        selectObjectName(name+"Surface")
        bpy.ops.object.delete()
        ob.select = True
        
        #Input objects
        #_Names are false if prop doesn't exist
        sxName = self.makeMeshCopy("silhouetteX", ob.silhouetteX, context)
        syName = self.makeMeshCopy("silhouetteY", ob.silhouetteY, context)
        szName = self.makeMeshCopy("silhouetteZ", ob.silhouetteZ, context)
        
        if sxName and syName:
            sy  = getObject(sxName)
            sx  = getObject(syName)
            
            verts, faces = self.getGeometry(sx, sy)
            
            #Delete temporary copies of silhouettes
            if (sx):
                sx.select = True
            if (sy):
                sy.select = True
            bpy.ops.object.delete()
        
        #Actually generate the mesh
        addMesh(name+"Surface", verts, faces)
        context.scene.objects[name+"Surface"].location = loc
        
        context.scene.objects.active = ob
        selectObjectName(ob.name)
        
        return{'FINISHED'}
    
    def getGeometry(self, sx, sy):
        verts = []
        faces = []
        
        xvals = []
        yvals = []
        
        xvals, yvals = self.findXYGrid(sx, xvals, yvals)
        xvals, yvals = self.findXYGrid(sy, xvals, yvals)
         
        xsize = len(xvals)
        ysize = len(yvals)
        
        projectionX = []
        projection = {}
        
        #Generate Intersects
        for i in range(xsize):
            xval = xvals[i]
            projectionX.append(IntersectLine(sx.data.vertices, 
                                            sx.data.edges, i, xval))
            
            iLine = IntersectLine(sy.data.vertices, sy.data.edges, i, xval)
            
            inList = self.findInsideList(iLine.intersects.values(), yvals)
            
            for j in range(ysize):
                yval = yvals[j]
                if inList[j]:
                    projection[(i,j)] = deepcopy(projectionX[i])
                    projection[(i,j)].setY(j, yval)
                else:
                    projection[(i,j)] = None

        #Generate Vertices
        index = 0
        for i in range(xsize):
            for j in range(ysize):
                if projection[(i,j)]:
                    for intersect in projection[(i,j)].intersects.values():
                        intersect.index = index
                        verts.append([intersect.hit, intersect.x, intersect.y])
                        index += 1
        
        #Connect Edges
        for i in range(xsize):
            for j in range(ysize):
                v11 = projection[(i,j)]
                if v11:
                    if j != ysize-1:
                        v12 = projection[(i,j+1)]
                        if v12:
                            for intersect in v11.intersects.values():
                                matches = v12.findConnected(intersect)
                                intersect.connectedPlusY = matches
                                for match in matches:
                                    match.connectedMinusY.append(intersect)
                                    
                    if i != xsize-1:
                        v21 = projection[(i+1,j)]
                        if v21:
                            for intersect in v11.intersects.values():
                                matches = v21.findConnected(intersect)
                                intersect.connectedPlusX = matches
                                for match in matches:
                                    match.connectedMinusX.append(intersect)
        
        #Generate Faces
        for i in range(xsize-1):
            for j in range(ysize-1):
                if i == 0 and j == 0:
                    print(projection[(i,j)])
                    print(projection[(i+1,j)])
                    print(projection[(i,j+1)])
                    print(projection[(i+1,j+1)])
                
                faces += self.detectFaceForSquare(projection[(i,j)], projection[(i+1,j+1)])
        
        #Finished        
        return verts, faces
    
    
    
    def detectFaceForSquare(self, swProjection, neProjection):
        faces = []
        
        #Starting With the bottom left corner of the square
        if swProjection:
            for sw in swProjection.intersects.values():
                
                #Search North over ALL 
                if sw.connectedPlusY:
                    for nw in sw.connectedPlusY:
                         
                        #Search West over ALL
                        if nw.connectedPlusX:
                            for ne in nw.connectedPlusX:
                                
                                #Search South over FIRST
                                if ne.connectedMinusY:
                                    for se in ne.connectedMinusY:
                                        #Make Quad
                                        faces.append([sw.index,
                                                      nw.index,
                                                      ne.index,
                                                      se.index])
                                else:
                                    #Make Tri
                                    faces.append([sw.index,
                                                  nw.index,
                                                  ne.index])
                        
                        #Search North over ALL 
                        elif sw.connectedPlusX:
                            for se in sw.connectedPlusX:
                                #Make Tri
                                faces.append([sw.index,
                                              nw.index,
                                              se.index])
                    
                #Search West over ALL
                elif sw.connectedPlusX:
                    for se in sw.connectedPlusX:
                        
                        #Search North over All
                        if se.connectedPlusY:
                            for ne in se.connectedPlusY:
                                #Make Tri
                                faces.append([sw.index,
                                              se.index,
                                              ne.index])
        
        return faces
                        
                            
#                    
#                        else:
#                            faces.append([sw.index,
#                                          sw.connectedPlusX.index,
#                                          sw.connectedPlusY.index])
#                    elif sw.connectedPlusY.connectedPlusX:
#                        faces.append([sw.index,
#                                      sw.connectedPlusY.connectedPlusX.index,
#                                      sw.connectedPlusY.index])
#                elif sw.connectedPlusX:
#                    
#                    if sw.connectedPlusX.connectedPlusY:
#                        faces.append([sw.index,
#                                      sw.connectedPlusX.index,
#                                      sw.connectedPlusX.connectedPlusY.index])
#
#        #Starting with the top left corner
#        elif projection[(i+1,j+1)]:
#            for ne in projection[(i+1,j+1)].intersects.values():
#                if ne.connectedMinusY and ne.connectedMinusX:
#                    faces.append([ne.index,
#                                  ne.connectedMinusY.index,
#                                  ne.connectedMinusX.index])
    
    
    def findInsideList(self, intersects, vals):
        vMax = len(vals)
        
        inList = []
        for v in vals:
            inList.append(False)
        
        hits = []
        hits2 = []
        
        for i in intersects:
            if i.isAcross:
                hits.append(i.hit)
            else:
                hits2.append(i.hit)
        
        for vIndex in range(vMax):
            if vals[vIndex] in hits2:
                inList[vIndex] = True
        
        for hit in hits:
            for vIndex in range(vMax):
                if hit < vals[vIndex]:
                    inList[vIndex] = not inList[vIndex]
                
        for hit in hits:
            for vIndex in range(vMax):
                if abs(hit - vals[vIndex]) <  ERROR_T:
                            inList[vIndex] = True         
        
        return inList
    
    def findXYGrid(self, ob, xvals, yvals):
        for vert in ob.data.vertices:
            x = vert.co.x
            y = vert.co.y
            if not x in xvals:
                xvals.append(x)
            if not y in yvals:
                yvals.append(y)
        
        xvals.sort()
        yvals.sort()
        
        newXvals = []
        newXvals.append(xvals[0])
        
        xmax = len(xvals)
        for i in range(xmax-1):
            if abs(xvals[i] - xvals[i+1]) > ERROR_T:
                newXvals.append(xvals[i+1])
        
        newYvals = []
        newYvals.append(yvals[0])
        
        ymax = len(yvals)
        for i in range(ymax-1):
            if abs(yvals[i] - yvals[i+1]) > ERROR_T:
                newYvals.append(yvals[i+1])
        
        return newXvals, newYvals
    
    def makeMeshCopy(self, name, val, context):
        if val and hasObject(val):
            ob = getObject(val)
            context.scene.objects.active = ob
            selectObjectName(ob.name)
            bpy.ops.object.duplicate()
            bpy.ops.object.convert(target='MESH')
            return context.object.name
        return False

class Intersect:
    ON_V1 = 1
    ON_V2 = 2
    ON_BOTH = 3
    INBETWEEN = 4
    
    def __init__(self, i, x):
        self.x = x
        self.y = None
        self.i = i
        self.j = None
        self.hit = None
        self.index = None

        self.vert = None
        self.vertCo = None
        self.onVert = None
        self.connected = []

        self.isAcross = True

        self.connectedPlusX = []
        self.connectedPlusY = []
        
        self.connectedMinusX = []
        self.connectedMinusY = []

    def __repr__(self):
        ret = "<Intersect at ("+str(self.i)+","+str(self.j)+") ID:"+str(self.index)+"> "
        ret += "\t vert #" + str(self.vert) + \
               " onVert:" + str(self.onVert) + \
               " connected=" + str(self.connected)

        ret += "\n\t hit=" +str(self.hit) +  \
               " x=" + str(self.x) + \
               " y=" + str(self.y) + \
               " isAcross=" + str(self.isAcross)

        if self.connectedPlusX:
            ret += "\n\tPlusX Connection ID: " 
            for i in self.connectedPlusX:
                ret += str(i.index)
        else:
            ret += "\n\tPlusX Connection: " + str(self.connectedPlusX)
        if self.connectedPlusY:
            ret += "\n\tPlusY Connection ID: " 
            for i in self.connectedPlusY:
                ret += str(i.index)
        else:
            ret += "\n\tPlusY Connection: " + str(self.connectedPlusX)


        return ret

    def intersectEdge(self, vert1, vert2, v1, v2):
        if abs(v1.x - self.x) < ERROR_T:
            if abs(v2.x - self.x) < ERROR_T:
                self.hit = v1.y
                self.onVert = self.ON_V1
                #Don't connect vertically
            else:
                self.hit = v1.y
                self.onVert = self.ON_V1
                self.connected.append(vert2)
        elif abs(v2.x - self.x) < ERROR_T:
            self.hit = v2.y
            self.onVert = self.ON_V2
            self.connected.append(vert1)

        elif v1.x < self.x < v2.x or v2.x < self.x < v1.x:
            self.hit = (v2.y-v1.y)*(self.x- v1.x)/(v2.x-v1.x) + v1.y
            self.onVert = self.INBETWEEN
            self.connected.append(vert1)
            self.connected.append(vert2)
        else:
            return None

        if self.onVert == self.ON_V1:
            self.vert = vert1
            self.vertCo = v1
        if self.onVert == self.ON_V2:
            self.vert = vert2
            self.vertCo = v2

        return self.hit
        
    def setY(self, j, y):
        self.j = j
        self.y = y
        
    def isOnVert(self):
        if self.onVert == None:
            print("intersect generated incorrectly")
            return False
        return (self.onVert == self.ON_V1 or self.onVert == self.ON_V2)
        

class IntersectLine:
    def __init__(self, verts, edges, i, x):
        self.x = x
        self.y = None
        self.i = i
        self.j = None
        
        self.intersects = {}
        
        self.findIntersectLine(verts, edges)
    
    def __repr__(self):
        ret = "<IntersectLine at (" + str(self.i) + "," + str(self.j)+")>\n"
        for i in self.intersects.values():
            ret += "\t" + str(i)+"\n"
        return ret
       
    def findIntersectLine(self, verts, edges):
        for edge in edges:
            vert1 = edge.vertices[0]
            vert2 = edge.vertices[1]
            
            v1 = verts[vert1].co
            v2 = verts[vert2].co
            
            for edge in edges:
                intersect = Intersect(self.i, self.x)
                hit = intersect.intersectEdge(vert1, vert2, v1, v2)
                
                if hit != None:
                    if hit in self.intersects:
                        oldCon = self.intersects[hit].connected
                        for vert in intersect.connected:
                            if not vert in oldCon:
                                oldCon.append(vert)
                    else:
                        self.intersects[hit] = intersect

            # Correctly set isAcross so we can to point in polygon correctly
            for intersect in self.intersects.values():
                if intersect.onVert == intersect.ON_V1 or intersect.onVert == intersect.ON_V2:
                    if len(intersect.connected) == 2:
                        c1 = verts[intersect.connected[0]].co
                        c2 = verts[intersect.connected[1]].co
                        if c1.x < intersect.x and c2.x < intersect.x:
                            intersect.isAcross = False
                        elif c1.x > intersect.x and c2.x > intersect.x:
                            intersect.isAcross = False

                                    
    def setY(self, j, y):
        self.j = j
        self.y = y
         
        for intersect in self.intersects.values():
            intersect.setY(j, y)
            
    def findConnected(self, intersect):
        #Should only have one match so always short circut
        
        #intersect is to our left or right
        if abs(intersect.x - self.x) < ERROR_T:
            #Check for common vertex
            if intersect.isOnVert():
                return self.findVert(intersect.vert)
            else:
                for vert in intersect.connected:
                    ret = self.findVert(vert)
                    if ret:
                        return ret
        
        #Intersct is abover or below us   
        elif abs(intersect.y - self.y) < ERROR_T:
            #Check for connected vertex
            for vert in intersect.connected:
                ret = self.findConnectedHelp(vert)
                if ret:
                   return ret
            
            ret = self.findConnectedHelp(intersect.vert)
            if ret:
                return ret
        
        #Intersect is on a diagonal with us 
        else:
            print("invalid intersect to compare")
        
        #No Matches
        return []
            
    def findVert(self, vert):
        matches = []
        
        for intersect in self.intersects.values():
            if intersect.isOnVert():
                if intersect.vert == vert:
                    matches.append(intersect)
            else:
                for v in intersect.connected:
                    if v == vert:
                        matches.append(intersect)
        
        return matches

    def findConnectedHelp(self, vert):
        matches = []
        
        for intersect in self.intersects.values():
            for v in intersect.connected:
                    if v == vert:
                        matches.append(intersect)
        
        return matches

def register():
    bpy.types.Object.silhouetteX = bpy.props.StringProperty(default = "")
    bpy.types.Object.silhouetteY = bpy.props.StringProperty(default = "")
    bpy.types.Object.silhouetteZ = bpy.props.StringProperty(default = "")
    
    bpy.utils.register_class(Panel)
    bpy.utils.register_class(MESH_OT_AddSilhouetteObject)
    bpy.utils.register_class(MESH_OT_GenerateMesh)
    bpy.utils.register_class(MESH_OT_Remove)  
    
def unregister():
    bpy.utils.unregister_class(HelloWorldPanel)
    bpy.utils.unregister_class(MESH_OT_AddSilhouetteObject)
    bpy.utils.unregister_class(MESH_OT_GenerateMesh)
    bpy.utils.unregister_class(MESH_OT_Remove)
    
if __name__ == "__main__":
    register()