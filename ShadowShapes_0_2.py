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

def addMesh(name, verts, edges, faces):
        if name:
            me = bpy.data.meshes.new(name+'Mesh')
            ob = bpy.data.objects.new(name, me)
            ob.location = Vector()
            
            scn = bpy.context.scene
            scn.objects.link(ob)
            scn.objects.active = ob
            ob.select = True
         
            me.from_pydata(verts, edges, faces)
            
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
        selectObjectName(name+"Surface2")
        bpy.ops.object.delete()
        ob.select = True
        
        #Input objects
        #_Names are false if prop doesn't exist
        sxName = self.makeMeshCopy("silhouetteX", ob.silhouetteX, context)
        syName = self.makeMeshCopy("silhouetteY", ob.silhouetteY, context)
        szName = self.makeMeshCopy("silhouetteZ", ob.silhouetteZ, context)
        
        if sxName and syName:
            # === Generate First surface ===
            sy  = getObject(sxName)
            sx  = getObject(syName)
            
            verts, edges, faces = self.getGeometry(sx, sy)
        
            #Actually generate the mesh
            addMesh(name+"Surface", verts, edges, faces)
            context.scene.objects[name+"Surface"].location = loc
            
            # === Generate Second Surface ===
            sx  = getObject(sxName)
            sy  = getObject(syName)
            
            verts2, edges2, faces2 = self.getGeometry(sx, sy)
            
            selectObjectName("NonExistant")
            #bpy.ops.object.select_all(action='TOGGLE')
            #Delete temporary copies of silhouettes
            if (sx):
                sx.select = True
            if (sy):
                sy.select = True
            bpy.ops.object.delete()
        
            #Actually generate the mesh
            addMesh(name+"Surface2", verts2, edges2, faces2)
            context.scene.objects[name+"Surface2"].location = loc
            
            selectObjectName("NonExistant")
            context.scene.objects[name+"Surface2"].select = True
            bpy.ops.transform.rotate(value=1.5708, axis=(0, 1, 0), constraint_orientation='GLOBAL')
            bpy.ops.transform.rotate(value=3.14159, axis=(1, 0, 0), constraint_orientation='GLOBAL')
            bpy.ops.transform.rotate(value=3.14159, axis=(0, 0, 1), constraint_orientation='GLOBAL')
            bpy.ops.transform.resize(value=(-1, 1, 1), constraint_orientation='GLOBAL')
        
        context.scene.objects.active = ob
        selectObjectName(ob.name)
        
        return{'FINISHED'}
    
    def getGeometry(self, sx, sy):
        verts = []
        edges = []
        faces = []
        
        xvals = []
        yvals = []
        
        projectionX = []
        projection = {}
        
        #Generate Initial Grid markings
        xvals, yvals = self.findXYGrid(sx, xvals, yvals)
        xvals, yvals = self.findXYGrid(sy, xvals, yvals)
        
        xext, yext = self.findExtraGridMarkings(sy.data.vertices, sy.data.edges, sx.data.vertices, 
                                                sx.data.edges, xvals, yvals)
        
        xsize = len(xvals)
        ysize = len(yvals)
        
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
        
        for lineList in xext.values():
            for line in lineList:
                for intersect in line.intersects.values():
                    intersect.index = index
                    verts.append([intersect.hit, intersect.x, intersect.y])
                    index += 1
                    
        for lineList in yext.values():
            for line in lineList:
                for intersect in line.intersects.values():
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
                                    edges.append([match.index, intersect.index])    
                                    match.connectedMinusY.append(intersect)
                                    
                    if i != xsize-1:
                        v21 = projection[(i+1,j)]
                        if v21:
                            for intersect in v11.intersects.values():
                                matches = v21.findConnected(intersect)
                                intersect.connectedPlusX = matches
                                for match in matches:
                                    edges.append([match.index, intersect.index])
                                    match.connectedMinusX.append(intersect)
        
        #Connect Edges to Extra Verts.
        for lineList in yext.values():
            for line in lineList:
                afterXIndex = 0
                yindex = 0
                
                for i in range(xsize):
                    xval = xvals[i]
                    if line.x < xval:
                        afterXIndex = i
                        break
                
                for j in range(ysize):
                    if abs(yvals[j] - line.y) < ERROR_T:
                        yindex = j
                
                line.i = afterXIndex - 0.5
                line.j = yindex
                
                afterLine = projection[(afterXIndex,yindex)]
                if afterLine:
                    for intersect in line.intersects.values():
                        matches = afterLine.findConnected(intersect)
                        intersect.connectedPlusX = matches
                        for match in matches:
                            edges.append([match.index, intersect.index])
                            match.connectedMinusX.append(intersect)
                
                beforeXIndex = afterXIndex -1
                if beforeXIndex >= 0:
                    beforeLine = projection[(beforeXIndex,yindex)]
                    if beforeLine:
                        for intersect in line.intersects.values():
                            matches = beforeLine.findConnected(intersect)
                            intersect.connectedMinusX = matches
                            for match in matches:
                                edges.append([match.index, intersect.index])
                                match.connectedPlusX.append(intersect)
                        #print("beforeLine\n", beforeLine)
                        #print("line\n", line)
        
        #Connect Edges to Extra Verts.
        for lineList in xext.values():
            for line in lineList:
                afterYIndex = 0
                xindex = 0
                
                for j in range(ysize):
                    yval = yvals[j]
                    if line.y < yval:
                        afterYIndex = j
                        break
                    
                for i in range(xsize):
                    if abs(xvals[i] - line.x) < ERROR_T:
                        xindex = i
                
                line.i = xindex
                line.j = afterYIndex - 0.5
                
                afterLine = projection[(xindex,afterYIndex)]
                if afterLine:
                    for intersect in line.intersects.values():
                        matches = afterLine.findConnected(intersect)
                        intersect.connectedPlusY = matches
                        for match in matches:
                            edges.append([match.index, intersect.index])
                            match.connectedMinusY.append(intersect)
                print("hi", afterLine, xindex, afterYIndex)
                
                beforeYIndex = afterYIndex -1
                if beforeYIndex >= 0:
                    beforeLine = projection[(xindex,beforeYIndex)]
                    if beforeLine:
                        for intersect in line.intersects.values():
                            matches = beforeLine.findConnected(intersect)
                            intersect.connectedMinusY = matches
                            for match in matches:
                                edges.append([match.index, intersect.index])
                                match.connectedPlusY.append(intersect)  
                        print("beforeLine\n", beforeLine)   
                        print("line\n", line)

        #Generate Faces
        for i in range(xsize-1):
            for j in range(ysize-1):
                faces += self.detectFaceForSquare(verts,
                                                  projection[(i,j)], 
                                                  projection[(i+1,j+1)])
        
        #Finished        
        return verts, edges, faces
    
    def findExtraGridMarkings(self, verts, edges, verts2, edges2, xvals, yvals):
        
        xExtra = {}
        yExtra = {}
        
        for edge in edges:
            vert1 = edge.vertices[0]
            vert2 = edge.vertices[1]
            
            v1 = verts[vert1].co
            v2 = verts[vert2].co
            
            for x in xvals:
                if v1.x+ERROR_T < x < v2.x-ERROR_T or \
                   v2.x+ERROR_T < x < v1.x-ERROR_T:
                    hit = (v2.y-v1.y)*(x- v1.x)/(v2.x-v1.x) + v1.y
                    
                    isect = IntersectLine(verts2, edges2, None, x)
                    isect.setY(None, hit)
                    
                    if x in xExtra:
                        xExtra[x].append(isect)
                    else:
                        xExtra[x] = [isect]
                    
            for y in yvals:
                if v1.y+ERROR_T < y < v2.y-ERROR_T or \
                   v2.y+ERROR_T < y < v1.y-ERROR_T:
                    hit = (v2.x-v1.x)*(y- v1.y)/(v2.y-v1.y) + v1.x
                    
                    isect = IntersectLine(verts2, edges2, None, hit)
                    isect.setY(None, y)
                    
                    if y in yExtra:
                        yExtra[y].append(isect)
                    else:
                        yExtra[y] = [isect]
                
        return xExtra, yExtra
    
    def removeDoubles(self, list):
        list.sort()
        max = len(list)
        newList = []
        
        newList.append(list[0])
        
        for i in range(max-1):
            if abs(list[i] - list[i+1]) > ERROR_T:
                newList.append(list[i+1])
                
        return newList
    
    def detectFaceForSquare(self, verts, swProjection, neProjection):
        faces = []
        
        #Starting With the bottom left corner of the square
        if swProjection:
            for sw in swProjection.intersects.values():
                
                #Search North over ALL 
                if sw.connectedPlusY:
                    for nw in sw.connectedPlusY:
                         
                        #Search East over ALL
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
                    
                #Search East over ALL
                elif sw.connectedPlusX:
                    for se in sw.connectedPlusX:
                        
                        #Search North over ALL
                        if se.connectedPlusY:
                            for ne in se.connectedPlusY:
                                #Make Tri
                                faces.append([sw.index,
                                              se.index,
                                              ne.index])
        
        #Start at far corner                              
        elif neProjection:
            for ne in neProjection.intersects.values():
                
                #Search South over ALL
                if ne.connectedMinusY:
                    for se in ne.connectedMinusY:
                        
                        #Search West over ALL
                        if ne.connectedMinusX:
                            for nw in ne.connectedMinusX:
                                
                                #Search for extra vert west
                                if se.connectedMinusX:
                                    for s in ne.connectedMinusX:
                                        
                                        #Search for extra vert west
                                        if nw.connectedMinusY:
                                            for w in nw.connectedMinusY:
                                                
                                                #Make Quint
                                                faces.append([se.index,
                                                              ne.index,
                                                              nw.index])
                                                faces.append([se.index,
                                                              nw.index,
                                                              w.index])
                                        else:
                                            #Make Quad
                                            faces.append([se.index,
                                                          ne.index,
                                                          nw.index,
                                                          s.index])
                                
                                elif nw.connectedMinusY:
                                    for w in nw.connectedMinusY:
                                        
                                        #Make Quad
                                        faces.append([se.index,
                                                      ne.index,
                                                      nw.index,
                                                      w.index])
                                
                                else:
                                    #Make Tri
                                    faces.append([se.index,
                                                  ne.index,
                                                  nw.index])
            
        return faces

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
                ret += str(i.index) + ", "
        else:
            ret += "\n\tPlusX Connection: " + str(self.connectedPlusX)
        
        if self.connectedPlusY:
            ret += "\n\tPlusY Connection ID: " 
            for i in self.connectedPlusY:
                ret += str(i.index) + ", "
        else:
            ret += "\n\tPlusY Connection: " + str(self.connectedPlusY)

        if self.connectedMinusX:
            ret += "\n\tMinusX Connection ID: " 
            for i in self.connectedMinusX:
                ret += str(i.index) + ", "
        else:
            ret += "\n\tMinusX Connection: " + str(self.connectedMinusX)
        
        if self.connectedMinusY:
            ret += "\n\tMinusY Connection ID: " 
            for i in self.connectedMinusY:
                ret += str(i.index) + ", "
        else:
            ret += "\n\tMinusY Connection: " + str(self.connectedMinusY)
        
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