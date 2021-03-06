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
#from math import sin, cos

#Debug Line
from time import ctime
print("-------------------",ctime(),"-------------------")

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
        print("\n+++++++++++++++++",ctime(),"+++++++++++++++++")
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
        
        verts = []
        faces = []
        
        old_xvals = None
        
        if sxName and syName:
            sy  = getObject(sxName)
            sx  = getObject(syName)
            
            yvals = set()
            zvals = set()
            
            for vert in sy.data.vertices:
                yvals.add(vert.co.x)
                
            for vert in sy.data.vertices:
                zvals.add(vert.co.y)
            
            yvals = list(yvals)
            zvals = list(zvals)
            
            yvals.sort()
            zvals.sort()
            
            ymax = len(yvals)
           
            ij_to_index = {}
            connected = {}
            
            index = 0
            
            for i in range(ymax):
                yval = yvals[i]
                
                #Precompute Intersections
                #yintersects = self.getLineIntersections(True, yval, 
                #                                        sx.data.vertices, 
                #                                        sx.data.edges)
                
                xintersects = self.getLineIntersections(True, yval, 
                                                        sy.data.vertices, 
                                                        sy.data.edges)
                #Debug
                print(xintersects)
                yintersects = xintersects
                
                #Grid of faces
                for j in range(len(zvals)):
                    zval = zvals[j]
                    
                    if self.isInSilhouette(zval, yintersects):
                        temp_verts = []
                        
                        
                        for key,val in xintersects.items():
                            xval = val[0]
                            
                            #Generate Vertex
                            print("add vertex", [xval,zval,yval], "index", index)
                            verts.append([xval,zval,yval])
                            temp_verts.append(index)
                            
                            if key[0]:
                                connected[index] = (key[0], key[1], val[1])
                            else:
                                connected[index] = (key[0], [key[1], key[2]])
                            index += 1
                     
                     
                        ij_to_index[(i,j)] = temp_verts
                        
                        
                        
                        
                        #Generate Faces
                        if i != 0 and j != 0:
                            a = ij_to_index[(i,j)]
                            b = ij_to_index[(i-1,j)]
                            c = ij_to_index[(i-1,j-1)]
                            d = ij_to_index[(i,j-1)]
                            
                            indexList = []
                            
                            self.grabValidIndexes(a, indexList)
                            self.grabValidIndexes(b, indexList)
                            self.grabValidIndexes(d, indexList)
                            self.grabValidIndexes(c, indexList)
                            
                            if len(indexList) > 2:
                                print("\nconnected", connected)
                                print("\nindexList", indexList)
                                face, remainder = self.findConnected(indexList[0], indexList, connected)
                                print("potential face", face,"remain:", remainder)
                                if len(face) > 2:
                                    tmp = face[0]
                                    face[0] = face[1]
                                    face[1] = tmp
                                    faces.append(face)
                                    
                                    
                                index = 0
                                while remainder and index < len(remainder):
                                    face, remainder = self.findConnected(remainder[index], remainder, connected)
                                    print("potential face", face,"remain:", remainder)
                                    if len(face) > 2:
                                        tmp = face[0]
                                        face[0] = face[1]
                                        face[1] = tmp
                                        faces.append(face)
                                        
                                    index += 1
                                        
                                        
                        
                    else:
                        ij_to_index[(i,j)] = False
                                
                                    
            #Delete temporary copies of silhouettes
            if (sx):
                sx.select = True
            if (sy):
                sy.select = True
            bpy.ops.object.delete()
        
        #Actually generate the mesh
        self.addMesh(name+"Surface", verts, faces)
        context.scene.objects[name+"Surface"].location = loc
        
        
        context.scene.objects.active = ob
        selectObjectName(ob.name)

        return{'FINISHED'}

    def findConnected(self, curr, indexList, connected):
        
        if indexList:
            a = connected[curr]
            
            if a[0]:
                adj, remainder = self.findAdjacent(a[1], indexList, connected)
            else:
                adj, remainder = self.findAdjacent(a[1][0], indexList, connected)
                if not adj:
                    adj, remainder = self.findAdjacent(a[1][1], indexList, connected)
            
            for i in adj:
                tempAdj, remainder = self.findConnected(i, remainder, connected)
                adj += tempAdj
            
            return adj, remainder
        
        else:
            return [], []                
                
    def findAdjacent(self, curr, indexList, connected):
        adjacent = []
        notAdjacent = []
            
        for i in indexList:
            b = connected[i]
            if b[0]:
                if curr in b[2]:
                    adjacent.append(i)
                else:
                    notAdjacent.append(i)
            else:
                if curr in b[1]:
                    adjacent.append(i)
                else:
                    notAdjacent.append(i) 
        
        return adjacent, notAdjacent
                      
    def grabValidIndexes(self, inputList, outputList):
        if inputList:
            #outputList.append(inputList[0])
            for index in inputList:
                outputList.append(index)

    def isInSilhouette(self, y, intersects):
        inS = False
        
        for val in intersects.values():
            yval = val[0]
            if yval < y:
                inS = not inS
            elif yval == y:  #FIXME change for CSG Tree
                return True
        return inS
        
    def makeMeshCopy(self, name, val, context):
        if val and hasObject(val):
            ob = getObject(val)
            context.scene.objects.active = ob
            selectObjectName(ob.name)
            bpy.ops.object.duplicate()
            bpy.ops.object.convert(target='MESH')
            return context.object.name
        return False
        
    def addMesh(self, name, verts, faces):
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
    
    def getLineIntersections(self, isX, val, verts, edges):
        intersects = {}
        
        for edge in edges:
            vert1 = edge.vertices[0]
            vert2 = edge.vertices[1]

            hit, key, connected = self.getIntersection(isX, vert1, vert2, val, verts)
            print(hit, key, connected)
            
            if hit:
                if key in intersects.keys():
                    if connected:
                        intersects[key][1].append(connected)
                        intersects[key][0] = hit
                else:
                    if connected:
                        intersects[key] = [hit, [connected]]
                    else:
                        intersects[key] = [hit, []]
                
                #if connected and key[0]:
                #    cKey = (True, connected)
                #    if  cKey in intersects.keys():
                #        intersects[cKey][1].append(key[1])
                #    else:
                #        intersects[cKey] = [None, [key[1]]]

        return intersects
    
    def getIntersection(self, isX, vert1, vert2, val, verts):
        v1 = verts[vert1].co
        v2 = verts[vert2].co
        
        hit = False
        key = False
        connected = None
        
        if isX:
            if v1.x == val:
                if v2.x == val:
                    hit = v1.y
                    key = (True, vert1)
                    connected = None      #Don't connect vertical surfaces
                else:
                    hit = v1.y
                    key = (True, vert1)
                    connected = vert2
                    
            elif v2.x == val:
                hit = v2.y
                key = (True, vert2)
                connected = vert1
            
            elif v1.x < val < v2.x or v2.x < val < v1.x:
                hit = (v2.y-v1.y)*(val- v1.x)/(v2.x-v1.x) + v1.y
                key = (False, vert1, vert2)
                connected = None

        else:
            print("This is broken")
       
        return hit,key, connected
    

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