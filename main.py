from vispy import app, gloo
from vispy.util import keys

import random


from quaternions import *
from cube import Cube
from spin import Spin



CUBE_SECTIONS = 3
PATTERN = "donuts"
SPINS_FOR_SCRAMBLE = 23

TICK = 0.10*1000.0/60.0
SPIN_TIME = 1

# rgba
X_COLOR = (1,0,0,1)
Y_COLOR = (0,1,0,1)
Z_COLOR = (0,0,1,1) 
MX_COLOR = (234/255,173/255,7/255,1)
MY_COLOR = (1,0,1,1)
MZ_COLOR = (1,1,0,1)

def random_color():
  return (random.random(),random.random(),random.random(),1)

class Canvas(app.Canvas):

    def __init__(self):
        super().__init__(size=(512, 512), title="Rubik's Cube",
                         keys='interactive')
        
        self.mp = False
        self.debounce=False
        self.do_ticks = True

        
        # setup gloo for rendering
        gloo.gl.glEnable(gloo.gl.GL_DEPTH_TEST)
        gloo.set_viewport(0, 0, *self.physical_size)
        gloo.set_clear_color('black')

        self.timer = app.Timer('auto',self.on_timer)
        self.now = 0
        self.quat = quat_empty()
        # self.clock=0
        self.timer.start()

        self.cube = Cube([X_COLOR,Y_COLOR,Z_COLOR,MX_COLOR,MY_COLOR,MZ_COLOR],CUBE_SECTIONS)

        #self.debug_print_cubes()

        self.spin_dir = self.cube.spin(1)
        self.status = {}

        self.show()

    def on_draw(self, event):
        gloo.clear()
        self.cube.draw(self.quat)

    def on_resize(self, event):
        gloo.set_viewport(0, 0, *event.physical_size)

    def on_timer(self,event):
      self.now = event.elapsed
      self.cube.tick(self.now)
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
      if event.key == keys.SPACE:
        if not self.debounce:
          self.do_ticks = not self.do_ticks
        self.debounce = True
      elif event.key == keys.Key("A") and self.cube.can_spin():
        self.do_spin(self.spin_dir)
        self.spin_dir = Cube.next_spin_in_pattern(PATTERN,self.spin_dir)
      elif event.key == keys.Key("S") and self.cube.can_spin():
        self.cube.scramble(SPINS_FOR_SCRAMBLE)
      elif event.key == keys.Key("1"):
        self.do_spin(Spin.X_CW)
      elif event.key == keys.Key("Q"):
        self.do_spin(Spin.X_CCW)
      elif event.key == keys.Key("2"):
        self.do_spin(Spin.Y_CW)
      elif event.key == keys.Key("W"):
        self.do_spin(Spin.Y_CCW)
      elif event.key == keys.Key("3"):
        self.do_spin(Spin.Z_CW)
      elif event.key == keys.Key("E"):
        self.do_spin(Spin.Z_CCW)
      elif event.key == keys.Key("4"):
        self.do_spin(Spin.MX_CW)
      elif event.key == keys.Key("R"):
        self.do_spin(Spin.MX_CCW)
      elif event.key == keys.Key("5"):
        self.do_spin(Spin.MY_CW)
      elif event.key == keys.Key("T"):
        self.do_spin(Spin.MY_CCW)
      elif event.key == keys.Key("6"):
        self.do_spin(Spin.MZ_CW)
      elif event.key == keys.Key("Y"):
        self.do_spin(Spin.MZ_CCW)
    
    def do_spin(self,direction):
      self.cube.start_spin(direction,SPIN_TIME,self.now)

    def on_key_release(self,event):
      if event.key== keys.SPACE:
        self.debounce = False

    def debug_print_cubes(self):
      for n in range(len(self.cubes)):
        cube = self.cubes[n]
        print("cube ",n)
        for i in range(len(cube["verts"])):
          print("pos: {0} \ncolor: {1}\n".format(cube["verts"][i],cube["colors"][i//4]))
          if i%4==3:
            print("\n")
  
if __name__ == '__main__':
    c = Canvas()
    app.run()