from vispy import gloo
import numpy as np


from quaternions import *
from spin import Spin




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

    self.spinning = False
    self.cubes = self.get_cubes(1,self.slices)
    self.indices = gloo.IndexBuffer(np.array([(0,1,2),(1,2,3)],dtype=np.uint32))

    # Build program
    self.program = gloo.Program(vertex, fragment)
    self.program['quat'] = get_quat(0,(1,1,1))
  
  def draw(self,global_quat):
    for cube in self.cubes:
      verts = []
      colors = []
      self.program['quat'] = quat_multiply(global_quat,quat_multiply(cube["anim_quat"],cube["spin"]))
      for i in range(len(cube["verts"])):
        verts.append(cube["verts"][i])
        colors.append(cube["colors"][i//4])
        if i%4==3:
          self.program['position']=verts
          self.program['color']=colors
          self.program.draw("triangles",self.indices)
          verts = []
          colors = []

  def tick(self,time_stamp):
    if self.spinning:
      spin_cubes = self.get_cubes_for_turn(self.spin_dir)

      time_interp=(time_stamp - self.spin_start)/self.spin_time

      # example = self.cubes[spin_cubes[0]['pos']]["anim_quat"]
      # ninety = get_quat(90,Cube.get_axis(self.spin_dir))
      # print(example)
      # print(ninety)
      # print()
      for idx in spin_cubes:
        cube = self.cubes[idx['pos']]
        if time_interp<1:
          cube["anim_quat"] = get_quat(90*time_interp,Cube.get_axis(self.spin_dir))
          pass
        else:
          cube["spin"] = quat_multiply(get_quat(90,Cube.get_axis(self.spin_dir)),cube["spin"])
          cube["anim_quat"] = quat_empty()
      if time_interp >= 1:
        self.cubes = Cube.apply_logical_rotation(spin_cubes,self.cubes,self.spin_dir.polarity())
        self.spinning = False

  def start_spin(self,direction,now,timespan):
    if self.can_spin():
      self.spin_dir = direction
      self.spin_start = now
      self.spin_time = timespan
      self.spinning = True

  def can_spin(self):
    return not self.spinning

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
            cubes.append({"verts":tc,"colors":colors,"spin":quat_empty(),"anim_quat":quat_empty()})
      return cubes   
  def spin(self,n):
    match n:
      case 1:
        return  Spin.X_CW
      case 2:
        return  Spin.Y_CW
      case 3:
        return  Spin.Z_CW
      case 4:
        return  Spin.MX_CW
      case 5:
        return  Spin.MY_CW
      case 6:
        return  Spin.MZ_CW
      case -1:
        return  Spin.X_CCW
      case -2:
        return  Spin.Y_CCW
      case -3:
        return  Spin.Z_CCW
      case -4:
        return  Spin.MX_CCW
      case -5:
        return  Spin.MY_CCW
      case -6:
        return  Spin.MZ_CCW
      case _:
        return  Spin.X_CW
  
  def get_axis(spin):
      match spin:
        case Spin.X_CCW:
          return (1,0,0)
        case Spin.X_CW:
          return (-1,0,0)
        case Spin.Y_CCW:
          return (0,-1,0)
        case Spin.Y_CW:
          return (0,1,0)
        case Spin.Z_CCW:
          return (0,0,1)
        case Spin.Z_CW:
          return (0,0,-1)
        case Spin.MX_CCW:
          return (1,0,0)
        case Spin.MX_CW:
          return (-1,0,0)
        case Spin.MY_CCW:
          return (0,-1,0)
        case Spin.MY_CW:
          return (0,1,0)
        case Spin.MZ_CCW:
          return (0,0,1)
        case Spin.MZ_CW:
          return (0,0,-1)
  
  def get_cubes_for_turn(self,spin):
    match spin:
      case Spin.X_CCW:
        return self.x_cube_ids
      case Spin.X_CW:
        return self.x_cube_ids
      case Spin.Y_CCW:
        return self.y_cube_ids
      case Spin.Y_CW:
        return self.y_cube_ids
      case Spin.Z_CCW:
        return self.z_cube_ids
      case Spin.Z_CW:
        return self.z_cube_ids
      case Spin.MX_CCW:
        return self.mx_cube_ids
      case Spin.MX_CW:
        return self.mx_cube_ids
      case Spin.MY_CCW:
        return self.my_cube_ids
      case Spin.MY_CW:
        return self.my_cube_ids
      case Spin.MZ_CCW:
        return self.mz_cube_ids
      case Spin.MZ_CW:
        return self.mz_cube_ids
    print("SPIN_ERROR")
    

  def next_spin_in_pattern(pattern,spin):
    match pattern:
      case "donuts"|"slices":
        match spin:
          case Spin.X_CW:
            return Spin.MX_CW
          case Spin.Y_CW:
            return Spin.MY_CW
          case Spin.Z_CW:
            return Spin.MZ_CW
          case Spin.MX_CW:
            return Spin.Y_CW
          case Spin.MY_CW:
            return Spin.Z_CW
          case Spin.MZ_CW:
            return Spin.X_CW
          case Spin.X_CCW:
            return Spin.MX_CCW
          case Spin.Y_CCW:
            return Spin.MY_CCW
          case Spin.Z_CCW:
            return Spin.MZ_CCW
          case Spin.MX_CCW:
            return Spin.Y_CCW
          case Spin.MY_CCW:
            return Spin.Z_CCW
          case Cube.Spin.MZ_CCW:
            return Cube.Spin.X_CCW
      case _:
        match self.spin:
          case Spin.X_CW:
            return Spin.Y_CW
          case Spin.Y_CW:
            return Spin.Z_CW
          case Spin.Z_CW:
            return Spin.MX_CW
          case Spin.MX_CW:
            return Spin.MY_CW
          case Spin.MY_CW:
            return Spin.MZ_CW
          case Spin.MZ_CW:
            return Spin.X_CCW
          case Spin.X_CCW:
            return Spin.Y_CCW
          case Spin.Y_CCW:
            return Spin.Z_CCW
          case Spin.Z_CCW:
            return Spin.MX_CCW
          case Spin.MX_CCW:
            return Spin.MY_CCW
          case Spin.MY_CCW:
            return Spin.MZ_CCW
          case Spin.MZ_CCW:
            return Spin.X_CW


  def apply_logical_rotation(indices,arr,is_cw):
    out = arr.copy()
    tag = 'prev' if is_cw else 'next'
    for i in indices:
      f = i['pos']
      t = i[tag]
      out[t] = arr[f]
    return out