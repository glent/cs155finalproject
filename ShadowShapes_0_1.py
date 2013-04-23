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
        ob.select = False
        selectObjectName("Surface")
        bpy.ops.object.delete()
        ob.select = True
        return{'FINISHED'}
    
class MESH_OT_GenerateMesh(bpy.types.Operator):
    bl_idname = "generate.obj"
    bl_label = "Generate Mesh"

    def execute(self, context):
        ob = context.object
        
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
            
            yvals = [vert.co.x for vert in sy.data.vertices]
            zvals = [vert.co.y for vert in sy.data.vertices] 
            
            ymax = len(yvals)
           
            dict = {}
            
            index = 0
            
            for i in range(ymax):
                yval = yvals[i]
                
                yintersects = self.getLineIntersections(True, yval, sx.data.vertices, sx.data.edges)
                
                xintersects = self.getLineIntersections(True, yval, 
                                                          sy.data.vertices, 
                                                          sy.data.edges)
                
                for j in range(len(zvals)):
                    zval = zvals[j]
                    
                    if self.isInSilhouette(zval, yintersects):
                        temp_verts = []
                        
                        for key,val in xintersects.items():
                            xval = val[0]
                            verts.append([xval,zval,yval])
                            temp_verts.append(index)
                            index += 1
                     
                     
                        dict[(i,j)] = temp_verts
            
                        if i != 0 and j != 0:
                            print(i,j)
                            
                            
                            a = dict[(i,j)]
                            b = dict[(i-1,j)]
                            c = dict[(i-1,j-1)]
                            d = dict[(i,j-1)]
                            
                            if a and b and c and d:
                                print(a,b,c,d)
                                faces.append([a[0],b[0],c[0],d[0]])
                            elif a and b and c:
                                faces.append([a[0],b[0],c[0]])
                            elif b and c and d:
                                faces.append([b[0],c[0],d[0]])
                            elif c and d and a:
                                faces.append([c[0],d[0],a[0]])
                            elif d and a and b:
                                faces.append([d[0],a[0],b[0]])
                                
                            
                    else:
                        dict[(i,j)] = False
                                
                                    
            #Delete temporary copies of silhouettes
            if (sx):
                sx.select = True
            if (sy):
                sy.select = True
            bpy.ops.object.delete()
        
        #Actually generate the mesh
        self.addMesh("Surface", verts, faces)
        
        context.scene.objects.active = ob
        selectObjectName(ob.name)

        return{'FINISHED'}

    def isInSilhouette(self, y, intersects):
        inS = False
        
        for val in intersects.values():
            yval = val[0]
            if yval > y:
                inS = not inS      
        
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
            
            if hit:
                if connected in intersects.keys():
                    intersects[key][1].append(connected)
                else:
                    intersects[key] = (hit, [connected])
                    
        return intersects
    
    def getIntersection(self, isX, vert1, vert2, val, verts):
        v1 = verts[vert1].co
        v2 = verts[vert2].co
        
        hit = False
        key = False
        connected = None
        
        if isX:
            if v1.x == val:
                hit = v1.y
                key = vert1
                connected = vert2
                
            elif v2.x == val:
                hit = v2.y
                key = vert2
                connected = vert1
            
            elif v1.x < val < v2.x or v2.x < val < v1.x:
                hit = (v2.y-v1.y)*(val- v1.x)/(v2.x-v1.x) + v1.y
                key = (vert1, vert2)
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