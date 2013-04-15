#Known Bugs
#Circular Interpolation doesn't use third reference values
#Circular Interpolation doesn't handle reference values properly

#=== Some Useful Helper Functions ===:

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
        print("Error: Cannot Return Property Value")
        print("Requested Property (" + propName + " does not exist")
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


def selectObjectName(objectName):
    for ob in bpy.data.objects:
        if ob.name == objectName:
            ob.select = True
        else:
            ob.select = False


def selectObjects(objectList):
    for ob in bpy.data.objects:
        if ob in objectList:
            ob.select = True
        else:
            ob.select = False


def getSelectedObjects():
    return [ob for ob in bpy.data.objects if ob.select]


# ---- Orientation ----
def getOrientation(ob):
    "Get the x y and z orientation vectors for object"
    #Get Euler Rotation
    currentRotationMode = ob.rotation_mode
    ob.rotation_mode = 'XYZ'
    rotation = ob.rotation_euler
    ob.rotation_mode = currentRotationMode

    #Declare Default Orientation Vectors
    x = Vector((1,0,0))
    y = Vector((0,1,0))
    z = Vector((0,0,1))

    #Apply Rotation to Orientation Vectors
    x.rotate(rotation)
    y.rotate(rotation)
    z.rotate(rotation)
    return x,y,z


def setOrientation(ob,x,y=None):
    "Use the x and y orientation vectors to set object rotation"
    #Find Y and Z components for Euler Rotation 
    x = Vector(x)
    quaternion = x.to_track_quat('X','Z') 
    euler = quaternion.to_euler()
    
    #Find X component for Euler Rotation
    if y:
        y = Vector(y)
        y_ref = Vector([0,1,0])
        y_ref.rotate(quaternion)
        angle = y_ref.angle(y)
        if ( y_ref.cross(y) ).dot(x) < 0:
            angle *= -1
        euler.rotate_axis('X',angle)

    #Apply Euler Rotation to Object
    currentRotationMode = ob.rotation_mode
    ob.rotation_mode = 'XYZ'
    ob.rotation_euler = euler
    ob.rotation_mode = currentRotationMode


# ---- String List Implementation ----
def strAppend(item,stringTarget):
    "Add item to list contained in stringTarget and update string"
    if hasProp(stringTarget):
        list = eval(getProp(stringTarget))
    else:
        list = []
    list.append(item)
    setProp(stringTarget,str(list))


def strRem(item, stringTarget):
    "Remove item from list contained in stringTarget and update string"
    list = eval(getProp(stringTarget))
    list.remove(item)
    setProp(stringTarget,str(list))


# ---- Mesh ----
def isMesh(ob):
    "Return True iff the object is a mesh"
    return ob.type == "MESH"


def findVerts(ob):
    "Return a list of vertex coordinates"
    list = []
    for v in ob.data.vertices:
        list.append([v.co[0],v.co[1],v.co[2]])
    return list


def getVertsAndVertConnections(ob):
    "Return a list vertex coordinates and connected vertex coordinates"
    listVerts = []
    
    for vert in ob.data.vertices:
        
        listConnections = []
        
        for edge in ob.data.edges:
            if vert.index in edge.vertices:
                for edgeVertIndex in edge.vertices:
                    if edgeVertIndex != vert.index:
                        listConnections.append(ob.data.vertices[edgeVertIndex].co)
            
        listVerts.append([vert.co, listConnections])

    return listVerts


def setVert(position,vert,default=[0,0,0]):
    "Move vertices to position with optional offset"
    vert.co[0] = default[0]+position[0]
    vert.co[1] = default[1]+position[1]
    vert.co[2] = default[2]+position[2]


# ---- Interpolation ----
def getPoint(id,pt):
    "Return value and position for desired pt on desired parameter"
    if pt == "default":
        return getProp(id+"t0_value"), \
               eval(getProp("default_verts"))
    return getProp(id+pt+"_value"), \
           eval(getProp(id+pt+"_verts"))


# ---- Linear Interpolation ----
def pickPoints(val,id,pt_list):
    i=0
    while True:
        valBefore, vertBefore = getPoint(id,pt_list[i])
        valAfter, vertAfter = getPoint(id,pt_list[i+1])
        
        if (valBefore <= val <= valAfter) or \
           ((i == 0 and val < valBefore) or \
           (i == len(pt_list)-2 and val > valAfter)):
            return valBefore, vertBefore, valAfter, vertAfter
        elif i == len(pt_list)-1:
            print("Error in pickPoints!")
        else:
            i += 1


def findParamOffset(val,val1,vert1,val2,vert2,vertDef):
    v1,v2 = Vector(vert1),Vector(vert2)
    
    if val2 == val1:
        v = v1
    else:    
        valDiff = (val - val1) / (val2 - val1)
        v = v1 + valDiff * (v2-v1)
    
    v -= Vector(vertDef)
    return list(v)


def applyParam(val,verts,valRef1,vertRef1,valRef2,vertRef2,vertDef,ob):
    if len(verts)==len(vertRef1)==len(vertRef2)==len(vertDef):
        for i in range(len(verts)):
            offset = findParamOffset(val,valRef2,vertRef2[i],valRef1,vertRef1[i],vertDef[i])
            verts[i][0] += offset[0]
            verts[i][1] += offset[1]
            verts[i][2] += offset[2]
        return verts 
    else:
        print("Error!")
        return verts


# ---- Circular Interpolation ----
def findCircleCenter(pointA,pointB,pointC):
    #Three position Vectors
    a = Vector(pointA)
    b = Vector(pointB)
    c = Vector(pointC)
    
    #Difference Consecutive
    d_ab = b-a
    d_bc = c-b
    
    #Normal Vector For Plane 
    n = d_bc.cross(d_ab)
    
    #Ignore if no center can be found
    if n.length == 0:
        return False
    
    #Midpoint Consecutive
    m_ab = (a+b)/2
    m_bc = (b+c)/2
    
    #Difference of Midpoints
    d_m = m_bc - m_ab
    
    #Direction to Center  (aka bisecting lines)
    c_ab = n.cross(d_ab)
    c_bc = n.cross(d_bc)
    
    d_center = c_ab * ( d_m.y - d_m.x * c_bc.y / c_bc.x ) / (c_ab.y - c_ab.x * c_bc.y / c_bc.x )
    
    center = m_ab + d_center
    return list(center)


def findParamOffsetCircle(val,vert,valA,vertA,valB,vertB,center):
    if valA == valB:
        return [0,0,0]
    
    #Convert to vectors
    a = Vector(vertB)    
    b = Vector(vertA)
    center = Vector(center)
    current = Vector(vert)
    
    #Standardize Parameter Value
    diff = (val - valA)/(valB - valA)
    
    #Vectors radiating from Center (difference)
    d_a = a - center
    d_b = b - center
    d_cur = current - center
    
    #Normal (For Rotation)
    n = d_b.cross(d_a)
    
    #Angles
    angle_ab = d_a.angle(d_b) #Always positive
    
    #Find orthogonal components adjusted for the current vector.
    n_cur = d_cur.project(n)
    a_cur = d_cur - n_cur
    b_cur = a_cur.cross(n)
    
    #a and b proportions
    factor_a = cos(diff * angle_ab)
    factor_b = -sin(diff * angle_ab)
    
    #Adjust a_cur and b_cur length
    cur_length = a_cur.length
    a_cur *= (cur_length * factor_a) / a_cur.length
    b_cur *= (cur_length * factor_b) / b_cur.length
    
    #Add Finished Componets
    d_ans = n_cur + a_cur + b_cur
    
    return list(d_ans - d_cur)


def pickPointsCircle(id,pt_list):
    "Return all three points value and vertex positions"
    valRef1,vertRef1 = getPoint(id,pt_list[0])
    valRef2,vertRef2 = getPoint(id,pt_list[1])
    valRef3,vertRef3 = getPoint(id,pt_list[2])
    return valRef1,vertRef1,valRef2,vertRef2,valRef3,vertRef3


def applyParamCircle(val,verts,valRef1,vertRef1,valRef2,vertRef2,valRef3,vertRef3,vertDef):
    if len(verts)==len(vertRef1)==len(vertRef2)==len(vertRef3)==len(vertDef):
        for i in range(len(verts)):
            center = findCircleCenter(vertRef1[i],vertRef2[i],vertRef3[i])
            if center:
                offset = findParamOffsetCircle(val,verts[i],
                                               valRef1,vertRef1[i],
                                               valRef2,vertRef2[i],
                                               center)
            else:
                offset = [0,0,0]  
            verts[i][0] += offset[0]
            verts[i][1] += offset[1]
            verts[i][2] += offset[2]
        return verts 
    else:
        print("Error!")
        return verts


#---- naming ----
def newName(stringTarget,context,normstring):
    i = 1
    if hasProp(stringTarget):    
        list = eval(getProp(stringTarget))

        while True:
            if normstring+str(i) in list:
                i+=1
            else:
                return normstring+str(i)
    
    return normstring+str(i)