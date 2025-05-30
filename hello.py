from vispy import app, gloo

import random


from quaternions import *
from cube import Cube



CUBE_SECTIONS = 3

TICK = 0.10*1000.0/60.0

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

        
        
        gloo.gl.glEnable(gloo.gl.GL_DEPTH_TEST)


        
        gloo.set_viewport(0, 0, *self.physical_size)
        gloo.set_clear_color('black')

        self.timer = app.Timer('auto',self.on_timer)
        self.quat = get_quat(0,(1,1,-1))
        self.clock=0
        self.timer.start()

        self.cube = Cube([X_COLOR,Y_COLOR,Z_COLOR,MX_COLOR,MY_COLOR,MZ_COLOR],CUBE_SECTIONS)

        #self.debug_print_cubes()

        self.spin = self.cube.spin(1)
        self.status = {}
        for i in self.Cube.Spin:
          self.status[i] = get_quat(0,(1,1,1))

        self.show()

    def on_draw(self, event):
        gloo.clear()
        self.cube.draw()

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