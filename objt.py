class Obj(object):
    def __init__(self, filename):
        with open(filename) as f:
            self.lines = f.read().splitlines()

        self.vertices = []
        self.faces = []
        self.read()

    def read(self):
        for line in self.lines:
            if line:
                prefix, value = line.split(' ', 1)
                #Determinar si es vector o cara
                if prefix == 'v':
                    self.vertices.append(
                        list(map(float, value.split(' ')))
                    )
                elif prefix == 'f':
                    #Hay modelos que tienen un espacio al final
                    if value[-1] == ' ':
                        value = value[:-1]
                    self.faces.append(
                        [list(map(int, face.split('/'))) for face in value.split(' ')]
                    )

