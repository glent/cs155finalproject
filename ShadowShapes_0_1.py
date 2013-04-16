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



#=== Operators ===
class MESH_OT_AddSilhouetteObject(bpy.types.Operator):
    bl_idname = "add.obj"
    bl_label = "Add Silhouette Object"

    def execute(self, context):
        bpy.ops.object.add(type = 'EMPTY')
        setProp("Silhouette", True)
        return{'FINISHED'}
    
class MESH_OT_GenerateMesh(bpy.types.Operator):
    bl_idname = "generate.obj"
    bl_label = "Generate Mesh"

    def execute(self, context):
        ob = context.object
        
        #Input objects
        #Names are false if prop doesn't exist
        sxName = self.makeMeshCopy("silhouetteX", ob.silhouetteX, context)
        syName = self.makeMeshCopy("silhouetteY", ob.silhouetteY, context)
        szName = self.makeMeshCopy("silhouetteZ", ob.silhouetteZ, context)
        
        verts = []
        faces = []
        
        if sxName and syName:
            sx  = getObject(sxName)
            sy  = getObject(syName)
            
            yvals = [vert.co.x for vert in sy.data.vertices]
            zvals = [vert.co.y for vert in sy.data.vertices] 
            #[vert.co.x for vert in sx.data.vertices] + 
            for yval in yvals:
                for zval in zvals:
                    xvals = self.getIntersections(True, zval, sx.data.vertices, sx.data.edges)
                    for xval in xvals:
                        verts.append([xval,yval,zval])
                    
        #Dummy Values for verticies and faces
        #verts = [[0,0,0],[1,0,0],[1,1,0]]
        #faces = [[0,1,2]]
        
        #FIXME set verts and faces to something smart.
        
        #Actually generate the mess
        self.addMesh("Surface", verts, faces)
        
        context.scene.objects.active = ob
        selectObjectName(ob.name)
        
        #FIXME deleat temporary copies of silhouettes
        
        return{'FINISHED'}
        
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
    
    def getIntersections(self, isX, val, verts, edges):
        intersects = [] 
        
        for edge in edges:
            v1 = verts[edge.vertices[0]].co
            v2 = verts[edge.vertices[1]].co
            
            if isX:
                if v1.x <= val <= v2.x or v2.x <= val <= v1.x:
                    intersects.append((v1.x - val)/(v1.x-v2.x)*v1.y + \
                                      (v2.x - val)/(v2.x-v1.x)*v2.y)                    
            else:
                if v1.y <= val <= v2.y or v2.y <= val <= v1.y:
                    intersects.append((v1.y - val)/(v1.y-v2.y)*v1.x + \
                                      (v2.y - val)/(v2.y-v1.y)*v2.x)

        return intersects

def register():
    bpy.types.Object.silhouetteX = bpy.props.StringProperty(default = "")
    bpy.types.Object.silhouetteY = bpy.props.StringProperty(default = "")
    bpy.types.Object.silhouetteZ = bpy.props.StringProperty(default = "")
    
    bpy.utils.register_class(Panel)
    bpy.utils.register_class(MESH_OT_AddSilhouetteObject)
    bpy.utils.register_class(MESH_OT_GenerateMesh)  
    
def unregister():
    bpy.utils.unregister_class(HelloWorldPanel)
    bpy.utils.unregister_class(MESH_OT_AddSilhouetteObject)
    bpy.utils.unregister_class(MESH_OT_GenerateMesh)
    
if __name__ == "__main__":
    register()
    
