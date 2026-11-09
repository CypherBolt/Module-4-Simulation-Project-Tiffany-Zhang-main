import random
import pgzrun

WIDTH = 800
HEIGHT = 600

GREEN = "#42f45f"
RED = "#f44141"

class Point: #an (x, y) on the screen
    def __init__(self, x, y):
        self.x = x #how far horizontally across the screen
        self.y = y #how far vertically down the screen

    def distance(self, other):
        if isinstance(other, Point):
            return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5 #pythagorean theorem
        return NotImplemented #in other words, we can't compare it so something that isn't a point

    def makeVectorTo(self, other):
        #builds a vector from one point to another
        if isinstance(other, Point):
            return Vector(other.x - self.x, other.y - self.y)
        return NotImplemented

    def move(self, vector):
        #shift point by vector 
        if isinstance(vector, Vector):
            self.x += vector.h
            self.y += vector.v
        else:
            raise TypeError("Expected a Vector")


class Vector:
    def __init__(self, h, v):
        self.h = h
        self.v = v

    def add(self, other):
        #combine two vectors
        if isinstance(other, Vector):
            self.h += other.h
            self.v += other.v
        return self

    def subtract(self, other):
        #remove one vector from another
        if isinstance(other, Vector):
            self.h -= other.h
            self.v -= other.v
        return self

    def multiply(self, scalar):
        #scale the vector by a scalar
        if isinstance(scalar, (int, float)):
            self.h *= scalar
            self.v *= scalar
        return self

    def divide(self, scalar):
        #scale the vector by a scalar
        if isinstance(scalar, (int, float)):
            self.h /= scalar
            self.v /= scalar
        return self

    def length(self):
        #pythagorean theorem
        return (self.h**2 + self.v**2) ** 0.5

    def normalize(self):
        #convert vector to unit vector
        length = self.length()
        if length > 0:
            self.h /= length
            self.v /= length
        else:
            #zero vector has no direction so keep at 0 to avoid division by zero
            self.h = 0
            self.v = 0
        return self


class Cell:
    def __init__(self, color):
        self.location = Point(0, 0)
        self.velocity = Vector(0, 0)
        self.size = 5
        self.color = color #green or red

    def move(self, cells): #move cells, bounce off walls, check for infection

        #move the cell using its velocity vector
        self.location.move(self.velocity)

        #keep cells inside screen boundaries and bounce them off walls
        if self.location.x < 0:
            self.location.x = 0
            self.velocity.h *= -1
        elif self.location.x > WIDTH:
            self.location.x = WIDTH
            self.velocity.h *= -1

        if self.location.y < 0:
            self.location.y = 0
            self.velocity.v *= -1
        elif self.location.y > HEIGHT:
            self.location.y = HEIGHT
            self.velocity.v *= -1

        #check for collisions with other cells
        for othercell in cells:
            if othercell == self:
                continue #cell can't infect itself

            #compute distance between cells
            distance = self.location.distance(othercell.location)

            #check if distance is less than the sum of their radii 
            if distance < (self.size + othercell.size):
                #if self is green and touches a red cell, turn red
                if self.color == GREEN and othercell.color == RED:
                    self.color = RED

    def draw_cell(self):
        screen.draw.filled_circle((self.location.x, self.location.y), self.size, self.color)


#create a global list of cells
cell_count = 50
cells = [] #holds every cell both healthy and infected

for cell in range(cell_count):
    #the first cell is red (patient zero), and the rest is green
    initial_color = RED if cell == 0 else GREEN
    cell = Cell(initial_color)

    #each cell is given a random starting point
    #keep cells a min of 20 pixels aways from the edges just so things run smoother
    cell.location = Point(random.randint(20, WIDTH - 20), random.randint(20, HEIGHT - 20))
    cell.velocity = Vector(random.uniform(-2, 2), random.uniform(-2, 2))
    cells.append(cell) #add cell to main list


def draw():
    screen.fill((0, 0, 0))
    screen.clear()
    for cell in cells:
        cell.draw_cell() #draw every cell in its current spot and color


def update():
    for cell in cells:
      cell.move(cells) #each cell moves, bounces, and checks for infection


pgzrun.go()