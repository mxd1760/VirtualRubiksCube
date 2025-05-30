import math

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