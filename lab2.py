#Juan Diego Solorzano 18151
#Lab2: Planeta

import struct
import math
from collections import namedtuple
from objt import Obj

V2 = namedtuple('Point2', ['x', 'y'])
V3 = namedtuple('Point3', ['x', 'y', 'z'])
white = bytes([255, 255, 255])
black = bytes([0, 0, 0])

def char(c):
    return struct.pack('=c', c.encode('ascii'))

def word(c):
    return struct.pack('=h', c)

def dword(c):
    return struct.pack('=l', c)

def glCreateWindow(width, height):
        win = Render(width, height)
        return win

def cross(v0, v1):
  #Producto cruz de 2 vectores
  return V3(
    v0.y * v1.z - v0.z * v1.y,
    v0.z * v1.x - v0.x * v1.z,
    v0.x * v1.y - v0.y * v1.x,
  )

def color(r, g, b):
    return(bytes([b, g, r]))

def bbox(*vertices):
  #Bounding box desde 2 vectores
  xs = [ vertex.x for vertex in vertices ]
  ys = [ vertex.y for vertex in vertices ]
  xs.sort()
  ys.sort()

  return V2(xs[0], ys[0]), V2(xs[-1], ys[-1])

def barycentric(A, B, C, P):
  #Conseguir coordenadas baricentricas desde los 3 vectores con producto cruz 
  cx, cy, cz = cross(
    V3(B.x - A.x, C.x - A.x, A.x - P.x), 
    V3(B.y - A.y, C.y - A.y, A.y - P.y)
  )

  if abs(cz) < 1:
      #es triangulo degenerado (regresar lo que sea)
    return -1, -1, -1

  u = cx/cz
  v = cy/cz
  w = 1 - (u + v)

  return w, v, u

def norm(v0):
  #Normal del vector
  v0length = length(v0)

  if not v0length:
    return V3(0, 0, 0)

  return V3(v0.x/v0length, v0.y/v0length, v0.z/v0length)

def dot(v0, v1):
  #Producto punto
  return v0.x * v1.x + v0.y * v1.y + v0.z * v1.z

def sub(v0, v1):
    #Resta de vectores
  return V3(v0.x - v1.x, v0.y - v1.y, v0.z - v1.z)

def length(v0):
  return (v0.x**2 + v0.y**2 + v0.z**2)**0.5

class Render(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.clearC = bytes([0, 0, 0])
        self.color = bytes([255, 255, 255])
        self.xw = 0
        self.yw = 0
        self.widthw = width
        self.heightw = height
        self.framebuffer = []
        self.poin = False
        self.rangem = False
        self.glClear()

        self.zbuffer = [
            [-999999 for x in range(self.width)]
            for y in range(self.height)
        ]

    def glInit(self, width, height):
        return
    
    #Area para pintar
    def glViewPort(self, x, y, width, height):
        self.xw = x
        self.yw = y
        self.widthw = width
        self.heightw = height

    #Pintar imagen   
    def glClear(self):
        self.framebuffer = [
            [self.clearC for x in range(self.width)]
            for y in range(self.height)
        ]

    #Color para pintar imagen
    def glClearColor(self, r, g, b):
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        self.clearC = bytes([b, g, r])
        self.glClear()

    #Crear archivo de la imagen
    def glFinish(self, filename):
        f = open(filename, 'bw')

        #file header
        f.write(char('B'))
        f.write(char('M'))
        f.write(dword(14 + 40 + self.width * self.height * 3))
        f.write(dword(0))
        f.write(dword(14 + 40))

        #image header
        f.write(dword(40))
        f.write(dword(self.width))
        f.write(dword(self.height))
        f.write(word(1))
        f.write(word(24))
        f.write(dword(0))
        f.write(dword(self.width * self.height * 3))
        f.write(dword(0))
        f.write(dword(0))
        f.write(dword(0))
        f.write(dword(0))

        #pixel data
        for x in range(self.height):
          for y in range(self.width):
            f.write(self.framebuffer[x][y])

        f.close()

    #Pintar punto
    def glVertex(self, x, y, color):
        if self.poin:
            xn = (x + 1)*(self.widthw/2) + self.xw
            yn = (y + 1)*(self.heightw/2) + self.yw
            xn = int(xn)
            yn = int(yn)
        else:
            xn = x
            yn = y
        self.framebuffer[yn][xn] = color

    #Color del punto
    def glColor(self, r, g, b):
        r = int(r * 255)
        g = int(g * 255)
        b = int(b * 255)
        self.color = bytes([b, g, r])

    def triangle(self, A, B, C, color):
        #bounding box
        bbox_min, bbox_max = bbox(A, B, C)

        for x in range(bbox_min.x, bbox_max.x + 1):
            for y in range(bbox_min.y, bbox_max.y + 1):
                w, v, u = barycentric(A, B, C, V2(x, y))
                #Ver si el punto esta dentro del triangulo basado en las caracteristicas dadas de las coordenadas (0 es valido)
                if w < 0 or v < 0 or u < 0:
                    #no lo pinta
                    continue

                z = A.z * w + B.z * v + C.z * u
                color = self.shader(x, y, z)
                if z > self.zbuffer[x][y]:

                    #pintar punto
                    self.glVertex(x, y, color)
                    self.zbuffer[x][y] = z

    #Pintar una linea de un punto a otro. Se optimizo el algoritmo evitando el uso de round y divisiones
    def glLine(self, x1, y1, x2, y2):
        #Cambiar valores
        self.poin = False

        #Modificar si se pidieron valores entre -1 y 1
        if self.rangem:
            x1n = int((x1 + 1)*(self.width/2))
            x2n = int((x2 + 1)*(self.width/2))
            y1n = int((y1 + 1)*(self.height/2))
            y2n = int((y2 + 1)*(self.height/2))

        else:
            
            x1n = x1
            y1n = y1
            x2n = x2
            y2n = y2
        dy = abs(y2n - y1n)
        dx = abs(x2n - x1n)
        emp = dy > dx

        if emp:
            x1n, y1n = y1n, x1n
            x2n, y2n = y2n, x2n

        if x1n > x2n:
            x1n, x2n = x2n, x1n
            y1n, y2n = y2n, y1n

        dy = abs(y2n - y1n)
        dx = abs(x2n - x1n)
        #Variable para ver cuando subir de y
        offset = 0
        threshold = dx
        y = y1n
        #Pintar puntos
        for x in range(x1n, x2n):
            if emp:
                self.glVertex(y, x, black)
            else:
                self.glVertex(x, y, black)

            offset += dy * 2
            if offset >= threshold:
                #Sumar si linea va para arriba, restar si va para abajo
                y += 1 if y1n < y2n else -1
                threshold += 2 * dx

    def shader(self, x, y ,z):
        #Colores a utilizar
        c1 = [20, 36, 169]
        c2 = [62, 84, 232]
        c3 = [62, 102, 249]
        c4 = [96, 129, 255]
        c5 = [137, 243, 255]

        #Gradiente de la derecha y parte superior
        if x > 305 and y > 280:
            dx = x - 335
            dy = y - 280
            dst = math.sqrt(dx**2 + dy**2)
            
            if dst >= 190:
                r = (250 - dst)/60
                return color(int(c2[0]*r),int(c2[1]*r), int(c2[2]*r))
            else:
                if y > 170:
                    dx = 335 - x
                    dy = y - 170
                    dst = math.sqrt(dx**2 + dy**2)
                    if dst >= 230:
                        r = (250 - dst)/20
                        r1 = int(c2[1] + 18*r)
                        r2 = int(c2[2] + 17*r)
                        return color(c3[0], r1, r2)
                    else:
                        #Remolino en el centro
                        if y > 320:
                            dx = 400 - x
                            dy = y - 50
                            dst = math.sqrt(dx**2 + dy**2)
                            if dst <= 285:
                                return color(c1[0], c1[1], c1[2])
                            elif dst <=295:
                                return color(c2[0], c2[1], c2[2])
                            elif dst <=297 and x < 400 and x > 370:
                                return color(c5[0], c5[1], c5[2])
                            else:
                                return color(c3[0], c3[1], c3[2])
                        else:
                            dx = 400 - x
                            dy = y - 550
                            dst = math.sqrt(dx**2 + dy**2)
                            if dst <= 245:
                                return color(c1[0], c1[1], c1[2])
                            elif dst <=248:
                                if x < 380 and x > 350:
                                    return color(c5[0], c5[1], c5[2])
                                else:
                                    return color(c2[0], c2[1], c2[2])
                            elif dst <=260:
                                return color(c2[0], c2[1], c2[2])
                            elif dst <=265:
                                if x < 400 and x > 330:
                                    return color(c5[0], c5[1], c5[2])
                                else:
                                    return color(c2[0], c2[1], c2[2])
                            else:
                                return color(c3[0], c3[1], c3[2])
                else:
                    return color(c3[0], c3[1], c3[2])
        
        else:
            #Gradiente de la parte izquierda
            if x > 270 and x < 295 and y > 230 and y < 260:
                dx = x - 270
                if y > 230:
                    dy = y - 230
                else:
                    dy = 260 - y
                dst = dx + dy
                if dst < 20:
                    #Triangulo de la izquierda inferior
                    return color(c4[0], c4[1], c4[2])
                else:
                    return color(c3[0], c3[1], c3[2])
            else:
                if y > 300:
                    dx = 335 - x
                    dy = y - 300
                    dst = math.sqrt(dx**2 + dy**2)
                    if dst > 100:

                        r = (120 - dst)/20
                        r1 = int(c2[1] + 18*r)
                        r2 = int(c2[2] + 17*r)
                        return color(c3[0], r1, r2)
                    else:
                        return color(c3[0], c3[1], c3[2])
                else:
                    if y > 100:
                        dx = x - 400
                        dy = y
                        dst = math.sqrt(dx**2 + dy**2)
                        
                        #Circulos de la parte inferior con gradiente
                        if dst >= 240:
                            if x > 503:
                                dx = x - 335
                                dy = y - 280
                                dst = math.sqrt(dx**2 + dy**2)
                                
                                if dst >= 190:
                                    r = (250 - dst)/60
                                    return color(int(c2[0]*r),int(c2[1]*r), int(c2[2]*r))
                                else:
                                    return color(c3[0], c3[1], c3[2])
                            else:
                                if dst <= 155:
                                    r = (155 - dst)/5
                                    r1 = int(c3[1] - 18*r)
                                    r2 = int(c3[2] - 17*r)
                                    return color(c3[0], r1, r2)
                                else:
                                    return color(c3[0], c3[1], c3[2])
                        elif dst >= 180:
                            r = (250 - dst)/70
                            r1 = int(c2[1] + 18*r)
                            r2 = int(c2[2] + 17*r)
                            return color(c3[0], r1, r2)

                        else:
                            r = (dst)/180
                            return color(int(c3[0]*r),int(c3[1]*r), int(c3[2]*r))
                                
                    else:
                        return color(c3[0], c3[1], c3[2])

                    
    def load(self, filename, translate, scale):
        model = Obj(filename)
        
        for face in model.faces:
            #Cuantas caras tiene el modelo
            vcount = len(face)

            vertices = []
            
            for j in range(vcount):
                vi1 = face[j][0] - 1
                vi2 = face[(j + 1) % vcount][0] - 1

                v1 = model.vertices[vi1]
                v2 = model.vertices[vi2]

                #Solo acepta enteros. Sumar el translate y multiplicar por scale para ajustar al display
                x1 = round((v1[0] + translate[0]) * scale[0])
                y1 = round((v1[1] + translate[1]) * scale[1])
                z1 = round((v1[2] + translate[2]) * scale[2])
                x2 = round((v2[0] + translate[0]) * scale[0])
                y2 = round((v2[1] + translate[1]) * scale[1])
                z2 = round((v2[2] + translate[2]) * scale[2])
                
                #self.glLine(x1, y1, x2, y2)
                vertices.append(V3(x1, y1, z1))

            if vcount == 3:
                #3 caras
                A = vertices[0]
                B = vertices[1]
                C = vertices[2] 

                #Pintar triangulo
                self.triangle(A, B, C, white)

            if vcount == 4:
                #4 caras
                A = vertices[0]
                B = vertices[1]
                C = vertices[2]
                D = vertices[3]

                #Pintar triangulo
                self.triangle(A, B, C, white)
                self.triangle(A, D, C, white)


bitmap = Render(800, 600)
bitmap.load('sphere.obj', translate=[1.13, 0.84, 1], scale=[350, 350, 350])
bitmap.glFinish('out2.bmp')
