


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


def random_spin():
  return random.choice(list(Cube.Spin))