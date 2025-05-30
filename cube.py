from vispy import gloo
import numpy as np

from quaternions import *

from enum import Enum


# cube should know it's global rotation and the parent should be able to adjust it
# cube should be able to be told to spin in any direction
# maybe the cube could have a function for animating the transitions

vertex = """
    attribute vec4 color;
    attribute vec3 position;
    uniform vec4 quat;

    varying vec4 v_color;
    void main()
    {
        float x = (position.x*(1-2*(quat.y*quat.y+quat.z*quat.z)) +position.y*2*(quat.x*quat.y-quat.z*quat.w)     +position.z*2*(quat.x*quat.z+quat.y*quat.w));
        float y = (position.x*2*(quat.x*quat.y+quat.z*quat.w)     +position.y*(1-2*(quat.x*quat.x+quat.z*quat.z)) +position.z*2*(quat.y*quat.z-quat.x*quat.w));
        float z = (position.x*2*(quat.x*quat.z-quat.y*quat.w)     +position.y*2*(quat.y*quat.z+quat.x*quat.w)     +position.z*(1-2*(quat.x*quat.x+quat.y*quat.y)));
        gl_Position = vec4(x,y,z, 1.0);
        v_color = color;
    } """

fragment = """
    varying vec4 v_color;
    void main()
    {
      gl_FragColor = v_color;
  } """

colors = np.array([(0, 1, 0, 1), (0, 1, 0, 1),(0, 1, 0, 1),(0, 1, 0, 1),
                           (1, 0, 0, 1),(1, 0, 0, 1),(1, 0, 0, 1),(1, 0, 0, 1),
                           (0, 0, 1, 1),(0, 0, 1, 1),(0, 0, 1, 1),(0, 0, 1, 1),
                           (1, 0, 1, 1),(1, 0, 1, 1),(1, 0, 1, 1),(1, 0, 1, 1),
                           (0, 1, 1, 1),(0, 1, 1, 1),(0, 1, 1, 1),(0, 1, 1, 1),
                           (1, 1, 0, 1),(1, 1, 0, 1),(1, 1, 0, 1),(1, 1, 0, 1),
                           ],dtype=np.float32)


def rotation_group_collector(first,x_off,y_off,side_length):
  y = []
  for i in range(side_length):
    x=[]
    for j in range(side_length):
      x.append(first+i*y_off+j*x_off)
    y.append(x)
  out=[]
  pos = read_2d_arr(y)
  next = right_2d_arr(y)
  prev =  left_2d_arr(y)
  for i in range(len(pos)):
    out.append({'pos':pos[i],'next':next[i],'prev':prev[i]})
  return out

def read_2d_arr(arr):
  out = []
  for i in arr:
    for j in i:
      out.append(j)
  return out

def left_2d_arr(arr):
  out = []
  l = len(arr)
  l2 = len(arr[0])
  for i in range(l2):
    for j in range(l):
      out.append(arr[j][l2-1-i])
  return out

def right_2d_arr(arr):
  out = []
  l = len(arr)
  l2 = len(arr[0])
  for i in range(l2):
    for j in range(l):
      out.append(arr[l-1-j][i])
  return out






class Cube:
  def __init__(self,colors,slices):
    self.slices = slices

    self.mx_color = colors[0]
    self.my_color = colors[1]
    self.mz_color = colors[2]
    self.x_color = colors[3]
    self.y_color = colors[4]
    self.z_color = colors[5]

    self.mx_cube_ids = rotation_group_collector(0,1,self.slices,self.slices)
    self.x_cube_ids = rotation_group_collector(self.slices*self.slices*(self.slices-1),1,self.slices,self.slices)
    self.my_cube_ids = rotation_group_collector(0,1,self.slices*self.slices,self.slices)
    self.y_cube_ids = rotation_group_collector(self.slices*(self.slices-1),1,self.slices*self.slices,self.slices)
    self.mz_cube_ids = rotation_group_collector(0,self.slices,self.slices*self.slices,self.slices)
    self.z_cube_ids = rotation_group_collector(self.slices-1,self.slices,self.slices*self.slices,self.slices)   

    

    self.cubes = self.get_cubes(1,self.slices)
    self.indices = gloo.IndexBuffer(np.array([(0,1,2),(1,2,3)],dtype=np.uint32))

    # Build program
    self.program = gloo.Program(vertex, fragment)
        
    self.program['quat'] = get_quat(0,(1,1,1))
  
  def draw(self):
    for cube in self.cubes:
      verts = []
      colors = []
      self.program['quat'] = quat_multiply(self.quat,cube["spin"])
      for i in range(len(cube["verts"])):
        verts.append(cube["verts"][i])
        colors.append(cube["colors"][i//4])
        if i%4==3:
          self.program['position']=verts
          self.program['color']=colors
          self.program.draw("triangles",self.I)
          verts = []
          colors = []



  def tiny_cube(self,x,y,z,min,max,section):
    tc = []
    colors = []
    #-x
    if x<=0:
      tc += [
        (min,min+y*section,min+z*section),
        (min,min+y*section,min+(z+1)*section),
        (min,min+(y+1)*section,min+z*section),
        (min,min+(y+1)*section,min+(z+1)*section)
      ]
      colors.append(self.mx_color)
    #-y
    if y<=0:
      tc += [
        (min+x*section,min,min+z*section),
        (min+(x+1)*section,min,min+z*section),
        (min+x*section,min,min+(z+1)*section),
        (min+(x+1)*section,min,min+(z+1)*section)    
      ]
      colors.append(self.my_color)
    #-z
    if z<=0:
      tc += [
        (min+x*section,min+y*section,min),
        (min+x*section,min+(y+1)*section,min),
        (min+(x+1)*section,min+y*section,min),
        (min+(x+1)*section,min+(y+1)*section,min)
      ]
      colors.append(self.mz_color)
    #+x
    if(min+(x+1)*section >= max):
      tc += [
        (max,min+y*section,min+z*section),
        (max,min+(y+1)*section,min+z*section),
        (max,min+y*section,min+(z+1)*section),
        (max,min+(y+1)*section,min+(z+1)*section)
      ]
      colors.append(self.x_color)
    #+y
    if(min+(y+1)*section>=max):
      tc += [
        (min+x*section,max,min+z*section),
        (min+x*section,max,min+(z+1)*section),
        (min+(x+1)*section,max,min+z*section),
        (min+(x+1)*section,max,min+(z+1)*section) 
      ]
      colors.append(self.y_color)
    #+z
    if(min+(z+1)*section>=max):
      tc += [
        (min+x*section,min+y*section,max),
        (min+(x+1)*section,min+y*section,max),
        (min+x*section,min+(y+1)*section,max),
        (min+(x+1)*section,min+(y+1)*section,max),
      ]
      colors.append(self.z_color)
    return tc,colors
  def get_cubes(self,scale,sections):
      n = scale/2
      o = scale/sections
      cubes = []
      for x in range(sections):
        for y in range(sections):
          for z in range(sections):
            #each tiny cube
            tc,colors = self.tiny_cube(x,y,z,-n,+n,o)
            cubes.append({"verts":tc,"colors":colors,"spin":get_quat(0,(1,1,1))})
      return cubes   
  def spin(self,n):
    match n:
      case 1:
        self.spin = Cube.Spin.X_CW
      case 2:
        self.spin = Cube.Spin.Y_CW
      case 3:
        self.spin = Cube.Spin.Z_CW
      case 4:
        self.spin = Cube.Spin.MX_CW
      case 5:
        self.spin = Cube.Spin.MY_CW
      case 6:
        self.spin = Cube.Spin.MZ_CW
      case -1:
        self.spin = Cube.Spin.X_CCW
      case -2:
        self.spin = Cube.Spin.Y_CCW
      case -3:
        self.spin = Cube.Spin.Z_CCW
      case -4:
        self.spin = Cube.Spin.MX_CCW
      case -5:
        self.spin = Cube.Spin.MY_CCW
      case -6:
        self.spin = Cube.Spin.MZ_CCW
      case _:
        self.spin = Cube.Spin.X_CW

  def get_axis(self):
      match self:
        case Cube.Spin.X_CCW:
          return (1,0,0)
        case Cube.Spin.X_CW:
          return (-1,0,0)
        case Cube.Spin.Y_CCW:
          return (0,-1,0)
        case Cube.Spin.Y_CW:
          return (0,1,0)
        case Cube.Spin.Z_CCW:
          return (0,0,1)
        case Cube.Spin.Z_CW:
          return (0,0,-1)
        case Cube.Spin.MX_CCW:
          return (1,0,0)
        case Cube.Spin.MX_CW:
          return (-1,0,0)
        case Cube.Spin.MY_CCW:
          return (0,-1,0)
        case Cube.Spin.MY_CW:
          return (0,1,0)
        case Cube.Spin.MZ_CCW:
          return (0,0,1)
        case Cube.Spin.MZ_CW:
          return (0,0,-1)

  def get_set(self):
    match self.spin:
      case Cube.Spin.X_CCW:
        return self.outer.x_cube_ids
      case Cube.Spin.X_CW:
        return self.outer.x_cube_ids
      case Cube.Spin.Y_CCW:
        return self.outer.y_cube_ids
      case Cube.Spin.Y_CW:
        return self.outer.y_cube_ids
      case Cube.Spin.Z_CCW:
        return self.outer.z_cube_ids
      case Cube.Spin.Z_CW:
        return self.outer.z_cube_ids
      case Cube.Spin.MX_CCW:
        return self.outer.mx_cube_ids
      case Cube.Spin.MX_CW:
        return self.outer.mx_cube_ids
      case Cube.Spin.MY_CCW:
        return self.outer.my_cube_ids
      case Cube.Spin.MY_CW:
        return self.outer.my_cube_ids
      case Cube.Spin.MZ_CCW:
        return self.outer.mz_cube_ids
      case Cube.Spin.MZ_CW:
        return self.outer.mz_cube_ids

  def polarity(self):
    return self.value>0

  def next(self):
    match self.spin:
      case Cube.Spin.X_CW:
        return Cube.Spin.Y_CW
      case Cube.Spin.Y_CW:
        return Cube.Spin.Z_CW
      case Cube.Spin.Z_CW:
        return Cube.Spin.MX_CW
      case Cube.Spin.MX_CW:
        return Cube.Spin.MY_CW
      case Cube.Spin.MY_CW:
        return Cube.Spin.MZ_CW
      case Cube.Spin.MZ_CW:
        return Cube.Spin.X_CCW
      case Cube.Spin.X_CCW:
        return Cube.Spin.Y_CCW
      case Cube.Spin.Y_CCW:
        return Cube.Spin.Z_CCW
      case Cube.Spin.Z_CCW:
        return Cube.Spin.MX_CCW
      case Cube.Spin.MX_CCW:
        return Cube.Spin.MY_CCW
      case Cube.Spin.MY_CCW:
        return Cube.Spin.MZ_CCW
      case Cube.Spin.MZ_CCW:
        return Cube.Spin.X_CW

  def next_in_pattern(self,pattern):
    match pattern:
      case _:
        match self.spin:
          case Cube.Spin.X_CW:
            return Cube.Spin.MX_CW
          case Cube.Spin.Y_CW:
            return Cube.Spin.MY_CW
          case Cube.Spin.Z_CW:
            return Cube.Spin.MZ_CW
          case Cube.Spin.MX_CW:
            return Cube.Spin.Y_CW
          case Cube.Spin.MY_CW:
            return Cube.Spin.Z_CW
          case Cube.Spin.MZ_CW:
            return Cube.Spin.X_CW
          case Cube.Spin.X_CCW:
            return Cube.Spin.MX_CCW
          case Cube.Spin.Y_CCW:
            return Cube.Spin.MY_CCW
          case Cube.Spin.Z_CCW:
            return Cube.Spin.MZ_CCW
          case Cube.Spin.MX_CCW:
            return Cube.Spin.Y_CCW
          case Cube.Spin.MY_CCW:
            return Cube.Spin.Z_CCW
          case Cube.Spin.MZ_CCW:
            return Cube.Spin.X_CCW



def apply_rotation(indices,arr,is_cw):
  out = arr.copy()
  tag = 'prev' if is_cw else 'next'
  for i in indices:
    f = i['pos']
    t = i[tag]
    out[t] = arr[f]
  return out