from vispy import app, gloo
from vispy.gloo import Program
import numpy as np
import math
import random
from enum import Enum

# take in point p
# take in vector of rotation
# take in angle of rotation
# convert vector to unit vector
# convert vector and angle to quaternion
# transform p to rotated value using q*p*-q


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


CUBE_SCALE = 1
CUBE_SECTIONS = 3

TICK = 0.05*1000.0/60.0

# rgba
X_COLOR = (1,0,0,1)
Y_COLOR = (0,1,0,1)
Z_COLOR = (0,0,1,1) 
MX_COLOR = (0,1,1,1)
MY_COLOR = (1,0,1,1)
MZ_COLOR = (1,1,0,1)

def gen_empty(CUBE_SECTIONS):
  out = []
  for i in range(CUBE_SECTIONS*CUBE_SECTIONS*CUBE_SECTIONS):
    out.append(0)
  return out

class Spin(Enum):
  X_CW=1
  Y_CW=2
  Z_CW=3
  MX_CW=4
  MY_CW=5
  MZ_CW=6
  X_CCW=-1
  Y_CCW=-2
  Z_CCW=-3
  MX_CCW=-4
  MY_CCW=-5
  MZ_CCW=-6

  def get_axis(self):
    match self:
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
    
  def get_set(self):
    match self:
      case Spin.X_CCW:
        return X_CUBES
      case Spin.X_CW:
        return X_CUBES
      case Spin.Y_CCW:
        return Y_CUBES
      case Spin.Y_CW:
        return Y_CUBES
      case Spin.Z_CCW:
        return Z_CUBES
      case Spin.Z_CW:
        return Z_CUBES
      case Spin.MX_CCW:
        return MX_CUBES
      case Spin.MX_CW:
        return MX_CUBES
      case Spin.MY_CCW:
        return MY_CUBES
      case Spin.MY_CW:
        return MY_CUBES
      case Spin.MZ_CCW:
        return MZ_CUBES
      case Spin.MZ_CW:
        return MZ_CUBES

  def polarity(self):
    return self.value>0

  def next(self):
    match self:
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

  def next_in_pattern(self,pattern):
    match pattern:
      case _:
        match self:
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
          case Spin.MZ_CCW:
            return Spin.X_CCW

def random_spin():
  return random.choice(list(Spin))

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

def apply_rotation(indices,arr,is_cw):
  out = arr.copy()
  tag = 'prev' if is_cw else 'next'
  for i in indices:
    f = i['pos']
    t = i[tag]
    out[t] = arr[f]
  return out

def random_color():
  return (random.random(),random.random(),random.random(),1)

MX_CUBES = rotation_group_collector(0,1,CUBE_SECTIONS,CUBE_SECTIONS)
X_CUBES = rotation_group_collector(CUBE_SECTIONS*CUBE_SECTIONS*(CUBE_SECTIONS-1),1,CUBE_SECTIONS,CUBE_SECTIONS)
MY_CUBES = rotation_group_collector(0,1,CUBE_SECTIONS*CUBE_SECTIONS,CUBE_SECTIONS)
Y_CUBES = rotation_group_collector(CUBE_SECTIONS*(CUBE_SECTIONS-1),1,CUBE_SECTIONS*CUBE_SECTIONS,CUBE_SECTIONS)
MZ_CUBES = rotation_group_collector(0,CUBE_SECTIONS,CUBE_SECTIONS*CUBE_SECTIONS,CUBE_SECTIONS)
Z_CUBES = rotation_group_collector(CUBE_SECTIONS-1,CUBE_SECTIONS,CUBE_SECTIONS*CUBE_SECTIONS,CUBE_SECTIONS)


colors = np.array([(0, 1, 0, 1), (0, 1, 0, 1),(0, 1, 0, 1),(0, 1, 0, 1),
                           (1, 0, 0, 1),(1, 0, 0, 1),(1, 0, 0, 1),(1, 0, 0, 1),
                           (0, 0, 1, 1),(0, 0, 1, 1),(0, 0, 1, 1),(0, 0, 1, 1),
                           (1, 0, 1, 1),(1, 0, 1, 1),(1, 0, 1, 1),(1, 0, 1, 1),
                           (0, 1, 1, 1),(0, 1, 1, 1),(0, 1, 1, 1),(0, 1, 1, 1),
                           (1, 1, 0, 1),(1, 1, 0, 1),(1, 1, 0, 1),(1, 1, 0, 1),
                           ],dtype=np.float32)



class Canvas(app.Canvas):

    def __init__(self):
        super().__init__(size=(512, 512), title="Rubik's Cube",
                         keys='interactive')
        
        self.mp = False
        self.debounce=False
        self.do_ticks = True

        self.cubes = get_cubes(CUBE_SCALE,CUBE_SECTIONS)
        self.I = gloo.IndexBuffer(np.array([(0,1,2),(1,2,3)],dtype=np.uint32))
        
        gloo.gl.glEnable(gloo.gl.GL_DEPTH_TEST)

        # Build program
        self.program = Program(vertex, fragment)
        
        self.program['quat'] = get_quat(0,(1,1,1))
        
        gloo.set_viewport(0, 0, *self.physical_size)
        gloo.set_clear_color('black')

        self.timer = app.Timer('auto',self.on_timer)
        self.quat = get_quat(0,(1,1,-1))
        self.clock=0
        self.timer.start()

        #self.debug_print_cubes()

        self.spin = Spin.X_CW
        self.status = {}
        for i in Spin:
          self.status[i] = get_quat(0,(1,1,1))

        self.show()

    def debug_print_cubes(self):
      for n in range(len(self.cubes)):
        cube = self.cubes[n]
        print("cube ",n)
        for i in range(len(cube["verts"])):
          print("pos: {0} \ncolor: {1}\n".format(cube["verts"][i],cube["colors"][i//4]))
          if i%4==3:
            print("\n")

    def on_draw(self, event):
        gloo.clear()
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

    def on_resize(self, event):
        gloo.set_viewport(0, 0, *event.physical_size)

    def on_timer(self,event):
      if self.do_ticks:
        self.clock += TICK
      
        spin_set = self.spin.get_set()
      
        for idx in spin_set:
          cube = self.cubes[idx['pos']]
          cube["spin"] = quat_multiply(get_quat(TICK,self.spin.get_axis()),cube["spin"])
        

        #self.quat = quat_multiply(self.quat,get_quat(TICK,(1,1,1)))

        while self.clock>90:
          self.clock-=90
          self.cubes = apply_rotation(spin_set,self.cubes,self.spin.polarity())
          #self.spin = random_spin()
          self.spin=self.spin.next_in_pattern("")
          #print(self.spin)

        self.update()

    def on_mouse_press(self,event):
      self.mp = True
      self.last_pos = event.pos

    def on_mouse_release(self,event):
      self.mp = False

    def on_mouse_move(self,event):
      if self.mp:
        delta_x = (event.pos[0]-self.last_pos[0])*0.1
        delta_y = (event.pos[1]-self.last_pos[1])*0.1
        self.quat = quat_multiply(get_quat(delta_x,(0,-1,0)),self.quat)
        self.quat = quat_multiply(get_quat(delta_y,(-1,0,0)),self.quat)
        self.last_pos = event.pos
        self.update()
      
    def on_key_press(self,event):
      if not self.debounce:
        self.do_ticks = not self.do_ticks
      self.debounce = True
    
    def on_key_release(self,event):
      self.debounce = False

def quat_multiply(q1,q2):
    x = q1[0]*q2[3]+q2[0]*q1[3]   +q1[1]*q2[2]-q2[1]*q1[2]
    y = q1[1]*q2[3]+q2[1]*q1[3]   +q1[2]*q2[0]-q2[2]*q1[0]
    z = q1[2]*q2[3]+q2[2]*q1[3]   +q1[0]*q2[1]-q2[0]*q1[1]
    w = q1[3]*q2[3]-q1[1]*q2[1]-q1[2]*q2[2]-q1[0]*q2[0]
    return (x,y,z,w)

def get_quat(angle_degrees,axis):
    next = normalize(axis)
    rads = angle_degrees*math.pi/180
    s = math.sin(rads/2)
    return (s*next[0],s*next[1],s*next[2],math.cos(rads/2))

def normalize(vec3):
    x=vec3[0]
    y=vec3[1]
    z=vec3[2]
    mag = math.sqrt(x*x+y*y+z*z)
    return (x/mag,y/mag,z/mag)

def get_cubes(scale,sections):
    n = scale/2
    o = scale/sections
    cubes = []
    for x in range(sections):
      for y in range(sections):
        for z in range(sections):
          #each tiny cube
          tc,colors = tiny_cube(x,y,z,-n,+n,o)
          cubes.append({"verts":tc,"colors":colors,"spin":get_quat(0,(1,1,1))})
    return cubes    
    
def tiny_cube(x,y,z,min,max,section):
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
    colors.append(MX_COLOR)
  #-y
  if y<=0:
    tc += [
      (min+x*section,min,min+z*section),
      (min+(x+1)*section,min,min+z*section),
      (min+x*section,min,min+(z+1)*section),
      (min+(x+1)*section,min,min+(z+1)*section)    
    ]
    colors.append(MY_COLOR)
  #-z
  if z<=0:
    tc += [
      (min+x*section,min+y*section,min),
      (min+x*section,min+(y+1)*section,min),
      (min+(x+1)*section,min+y*section,min),
      (min+(x+1)*section,min+(y+1)*section,min)
    ]
    colors.append(MZ_COLOR)
  #+x
  if(min+(x+1)*section >= max):
    tc += [
      (max,min+y*section,min+z*section),
      (max,min+(y+1)*section,min+z*section),
      (max,min+y*section,min+(z+1)*section),
      (max,min+(y+1)*section,min+(z+1)*section)
    ]
    colors.append(X_COLOR)
  #+y
  if(min+(y+1)*section>=max):
    tc += [
      (min+x*section,max,min+z*section),
      (min+x*section,max,min+(z+1)*section),
      (min+(x+1)*section,max,min+z*section),
      (min+(x+1)*section,max,min+(z+1)*section) 
    ]
    colors.append(Y_COLOR)
  #+z
  if(min+(z+1)*section>=max):
    tc += [
      (min+x*section,min+y*section,max),
      (min+(x+1)*section,min+y*section,max),
      (min+x*section,min+(y+1)*section,max),
      (min+(x+1)*section,min+(y+1)*section,max),
    ]
    colors.append(Z_COLOR)
  return tc,colors
  
if __name__ == '__main__':
    c = Canvas()
    app.run()