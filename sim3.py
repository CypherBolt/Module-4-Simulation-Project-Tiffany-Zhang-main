import random
import pgzrun
import math
import os
import sys

#DISCLAIMER: RUNNING THIS ONE WILL NOT PLAY AFTER 150 TRIALS BECAUSE IT HAS REACHED ITS MAX LIMIT
#INSTEAD, PLEASE RUN demosim3.py TO see sim3.py in action!!

WIDTH = 800
HEIGHT = 600

GREEN = "#42f45f"
RED = "#f44141"

#this sim will have a probabilistic chance of infection with a cooldown to prevent multiple "rolls" from happening consecutively
infection_cooldown = 60 #frames a red cell waits before trying to infect the same cell again
infection_chance = 0.2 #20% of infection 

WALL_MARGIN = 10 #how close (in pixels) to a wall counts as "pressed against it"
MIN_SPEED = 0.5 #a wandering cell slower than this gets a fresh push so it never stalls

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
        self.attempt_cooldown = {} #frames left before valid for infection

    def slide_along_walls(self, direction):
        #if a cell is pressed against a wall and wants to run INTO it, cancel that part of
        #the movement so it slides along the wall instead of being pinned against it
        x = self.location.x
        y = self.location.y

        into_left = x <= WALL_MARGIN and direction.h < 0
        into_right = x >= WIDTH - WALL_MARGIN and direction.h > 0
        into_top = y <= WALL_MARGIN and direction.v < 0
        into_bottom = y >= HEIGHT - WALL_MARGIN and direction.v > 0

        blocked_x = into_left or into_right #can't run sideways any further
        blocked_y = into_top or into_bottom #can't run up/down any further

        #remember which way the red cell was pushing before we cancel anything
        push_h = direction.h
        push_v = direction.v

        if blocked_x:
            direction.h = 0
        if blocked_y:
            direction.v = 0

        #if almost nothing is left, the red cell was pushing it straight into the wall (or into a corner)
        #to combat this, i had to pick a direction along the wall myself
        if direction.length() < 0.3:
            # "toward the middle" of the screen, which keeps cells from drifting into corners
            toward_middle_x = 1 if x < WIDTH / 2 else -1
            toward_middle_y = 1 if y < HEIGHT / 2 else -1

            if blocked_x and blocked_y:
                #corner: slide along whichever wall the red cell is LESS in the way of
                if abs(push_h) < abs(push_v):
                    direction.h = toward_middle_x
                else:
                    direction.v = toward_middle_y
            elif blocked_x:
                #against a left/right wall: slide up or down (keep running away from the red if it's clear which way)
                if abs(push_v) > 0.05:
                    direction.v = 1 if push_v > 0 else -1
                else:
                    direction.v = toward_middle_y
            elif blocked_y:
                #against a top/bottom wall: slide left or right
                if abs(push_h) > 0.05:
                    direction.h = 1 if push_h > 0 else -1
                else:
                    direction.h = toward_middle_x

        return direction.normalize()

    def bounce_off_walls(self):
        #keep the cell inside the screen. Only flip the velocity if the cell is actually heading INTO the wall
        if self.location.x < 0:
            self.location.x = 0
            self.velocity.h = abs(self.velocity.h)
        elif self.location.x > WIDTH:
            self.location.x = WIDTH
            self.velocity.h = -abs(self.velocity.h)

        if self.location.y < 0:
            self.location.y = 0
            self.velocity.v = abs(self.velocity.v)
        elif self.location.y > HEIGHT:
            self.location.y = HEIGHT
            self.velocity.v = -abs(self.velocity.v)

    def move(self, cells): #move cells, bounce off walls, interact within 50 PX
        for cell in list(self.attempt_cooldown):
            #count down the cooldowns
            self.attempt_cooldown[cell] -= 1
            if self.attempt_cooldown[cell] <= 0:
                del self.attempt_cooldown[cell]
        
        target = None
        min_distance = 50 #interaction threshold

        if self.color == RED:
            #find the nearest uninfected cell within 50 pixels to chase
            for othercell in cells:
                if othercell.color == GREEN:
                    distance = self.location.distance(othercell.location)
                    if distance < min_distance:
                        min_distance = distance
                        target = othercell

            #if a target is found, chase it
            if target is not None:
                direction = self.location.makeVectorTo(target.location)
                direction.normalize()
                self.velocity = direction.multiply(3.0) # Red chase speed

        elif self.color == GREEN:
            #find the nearest infected cell within 50 pixels to flee from
            for othercell in cells:
                if othercell.color == RED:
                    distance = self.location.distance(othercell.location)
                    if distance < min_distance:
                        min_distance = distance
                        target = othercell

            #if a red cell is nearby, run away from it
            if target is not None:
                #vector pointing away from the red cell
                direction = target.location.makeVectorTo(self.location)
                direction.normalize()
                direction = self.slide_along_walls(direction) #don't run into a wall and get pinned
                self.velocity = direction.multiply(1.5) # Green flee speed

        #a cell with no target just keeps drifting, but if it has (almost) stopped, give it a new random push
        if target is None and self.velocity.length() < MIN_SPEED:
            angle = random.uniform(0, 2 * math.pi)
            self.velocity = Vector(math.cos(angle), math.sin(angle))

        self.location.move(self.velocity)

        #keep cells inside screen boundaries and bounce them off walls
        self.bounce_off_walls()

        #handle collisions with other cells
        for othercell in cells:
            if othercell == self:
                continue #cell can't collide with itself

            distance = self.location.distance(othercell.location)
            collision_distance = self.size + othercell.size

            if distance <= collision_distance and distance > 0:
                #push cells apart so they don't stick together
                overlap = collision_distance - distance
                nx = (self.location.x - othercell.location.x) / distance
                ny = (self.location.y - othercell.location.y) / distance
                
                #separate them equally
                self.location.x += nx * overlap * 0.5
                self.location.y += ny * overlap * 0.5
                othercell.location.x -= nx * overlap * 0.5
                othercell.location.y -= ny * overlap * 0.5

                #the push can shove a cell off the edge, so put both back inside the screen
                self.bounce_off_walls()
                othercell.bounce_off_walls()

                #bounce: if this cell is still heading INTO the cell it hit, reflect its velocity..
                #Without this, two cells drifting head-on just push against each other and freeze in place.......
                approach = self.velocity.h * nx + self.velocity.v * ny
                if approach < 0:
                    self.velocity.h -= 2 * approach * nx
                    self.velocity.v -= 2 * approach * ny

                #only roll if this red cell isn't still "cooling down" for this specific green cell
                if self.color == RED and othercell.color == GREEN:
                    if othercell not in self.attempt_cooldown:
                        self.attempt_cooldown[othercell] = infection_cooldown #start the cooldown
                        if random.random() < infection_chance:
                            othercell.color = RED

  
    def draw_cell(self):
        screen.draw.filled_circle((self.location.x, self.location.y), self.size, self.color)


#create a global list of cells
cell_count = 50

DATA_FILE = "demosim3_data.txt" 
TRIALS_NEEDED = 150 #collect at least this many trials before stopping


def make_cells():
    #builds a fresh batch of cells for a new trial
    new_cells = []
    for i in range(cell_count):
        #the first cell is red (patient zero), and the rest is green
        initial_color = RED if i == 0 else GREEN
        cell = Cell(initial_color)

        #each cell is given a random starting point
        #keep cells a min of 20 pixels aways from the edges just so things run smoother
        cell.location = Point(random.randint(20, WIDTH - 20), random.randint(20, HEIGHT - 20))
        cell.velocity = Vector(random.uniform(-2, 2), random.uniform(-2, 2))
        new_cells.append(cell) #add cell to main list
    return new_cells


def count_existing_trials():
    #so re-running the sim resumes instead of overwriting past data
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return sum(1 for line in f if line.strip())
    return 0


cells = make_cells() #holds every cell both healthy and infected
frame_count = 0 #frames elapsed in the current trial
trial_count = count_existing_trials() #trials already recorded in the data file


def draw():
    screen.clear()
    for cell in cells:
        cell.draw_cell() #draw every cell in its current spot and color


def update():
    global cells, frame_count, trial_count

    if trial_count >= TRIALS_NEEDED:
        return #this is because we already have enough data, so we stop simulating

    frame_count += 1
    for cell in cells:
        cell.move(cells) #each cell moves, bounces, and checks for infection

    if all(cell.color == RED for cell in cells):
        #virus has infected every cell, record how long it took
        seconds = frame_count / 60 #60 fps
        with open(DATA_FILE, "a") as f:
            f.write(f"{seconds}\n")

        trial_count += 1
        frame_count = 0
        cells = make_cells() #start the next trial automatically

        if trial_count >= TRIALS_NEEDED:
            print(f"Collected {trial_count} trials. Data saved to {DATA_FILE}.")
            sys.exit()


pgzrun.go()