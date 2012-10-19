#IGNORE:C0301
import sys, math
import pyglet
from pyglet.gl import *
import pymunk
from pymunk.vec2d import Vec2d
import world

def cpfclamp(f, min_, max_):
    """Clamp f between min and max"""
    return min(max(f, min_), max_)

def cpflerpconst(f1, f2, d):
    """Linearly interpolate from f1 to f2 by no more than d."""
    return f1 + cpfclamp(f2 - f1, -d, d)

pyglet.options['debug_gl'] = False
WIDTH, HEIGHT = 800, 600
FPS = 60
DT = 1./FPS
PLAYER_VELOCITY = 100. *2.
PLAYER_GROUND_ACCEL_TIME = 0.05
PLAYER_GROUND_ACCEL = (PLAYER_VELOCITY/PLAYER_GROUND_ACCEL_TIME)
PLAYER_AIR_ACCEL_TIME = 0.25
PLAYER_AIR_ACCEL = (PLAYER_VELOCITY/PLAYER_AIR_ACCEL_TIME)
JUMP_HEIGHT = 16.*3
JUMP_BOOST_HEIGHT = 24.
JUMP_CUTOFF_VELOCITY = 100
FALL_VELOCITY = 250.
JUMP_LENIENCY = 0.05
HEAD_FRICTION = 0.7
PLATFORM_SPEED = 1

class Main(pyglet.window.Window):
    is_event_handler = True
    def __init__(self):
        platform = pyglet.window.get_platform()
        display = platform.get_default_display()
        screen = display.get_default_screen()
        template = pyglet.gl.Config(double_buffer=True)
        config = screen.get_best_config(template)
        context = config.create_context(None)
        self.clock = pyglet.clock.Clock()
        self.kb_handler = pyglet.window.key.KeyStateHandler()
        super(Main, self).__init__(resizable=True, width=WIDTH, height=HEIGHT, caption="pymunk test" , context=context)
        self.push_handlers(self.kb_handler)
        self.batch = pyglet.graphics.Batch()
        self.direction = 1
        self.remaining_jumps = 2
        self.landing = {'p':Vec2d.zero(), 'n':0}
        self.landed_previous = False
        # box walls 
        self.space = world.World()
        
        def passthrough_handler(space, arbiter):
            if arbiter.shapes[0].body.velocity.y < 0:
                return True
            else:
                return False
                
        self.space.add_collision_handler(1,2, begin=passthrough_handler)
        # player
        self.body = pymunk.Body(5, pymunk.inf)
        self.body.position = 100,100
        self.head = pymunk.Circle(self.body, 10, (0,5))
        self.head2 = pymunk.Circle(self.body, 10, (0,13))
        self.feet = pymunk.Circle(self.body, 10, (0,-5))
        self.head.layers = self.head2.layers = 0b1000
        self.feet.collision_type = 1
        self.feet.ignore_draw = self.head.ignore_draw = self.head2.ignore_draw = True
        self.space.add(self.body, self.head, self.feet, self.head2)
        self.target_vx = 0

    def on_key_press(self, k, m):
        if k == pyglet.window.key.ESCAPE:
            sys.exit()
        elif k == pyglet.window.key.D:
            self.feet.ignore_draw = not self.feet.ignore_draw
            self.head.ignore_draw = not self.head.ignore_draw
            self.head2.ignore_draw = not self.head2.ignore_draw
        elif k == pyglet.window.key.UP:
            if self.well_grounded or self.remaining_jumps > 0:                    
                jump_v = math.sqrt(2.0 * JUMP_HEIGHT * abs(self.space.gravity.y)) #IGNORE:E1101
                self.body.velocity.y = self.ground_velocity.y + jump_v;
                self.remaining_jumps -=1
        
    def on_key_release(self, k, m):
        if k == pyglet.window.key.UP:
            self.body.velocity.y = min(self.body.velocity.y, JUMP_CUTOFF_VELOCITY)
            
    def draw_lines(self):
        self.batch = pyglet.graphics.Batch()
        for shape in self.space.shapes:
        #shape.body.is_static and
            if  isinstance(shape, pymunk.Segment):
                body = shape.body
                pv1 = body.position + shape.a.rotated(body.angle)
                pv2 = body.position + shape.b.rotated(body.angle)
                self.batch.add(2, GL_LINES, None, 
                ('v2f', (pv1.x, pv1.y, pv2.x, pv2.y)),
                ('c4f', (1.0, 1.0, 1.0, 1.) * 2))
            elif isinstance(shape, pymunk.Poly):
                ps = shape.get_points()
                ps = [ps[0]] + ps + [ps[0], ps[0]]
                xs = []
                for p in ps:
                    xs.append(p.x)
                    xs.append(p.y)
                self.batch.add(len(ps), GL_LINE_STRIP, None, 
                        ('v2f', xs),
                         ('c4f', (0.0, 1.0, 0.0, 1.0) * len(ps)))
                                      
            elif isinstance(shape, pymunk.Circle):
                p = shape.body.position
                ps = [p + (0,shape.radius), p + (shape.radius,0),
                        p + (0,-shape.radius), p + (-shape.radius,0)]
                ps += [ps[0]]
                xs = []
                for p in ps:
                    xs.append(p.x)
                    xs.append(p.y)
                self.batch.add(len(ps), GL_LINE_STRIP, None,
                         ('v2f', xs),
                          ('c4f', (0.0, 0.0, 1.0, 1.0) * len(ps)))

    def movement(self):
        grounding = {
            'normal' : Vec2d.zero(),
            'penetration' : Vec2d.zero(),
            'impulse' : Vec2d.zero(),
            'position' : Vec2d.zero(),
            'body' : None
        }
        # find out if player is standing on ground
        def f(arbiter):
            n = -arbiter.contacts[0].normal
            if n.y > grounding['normal'].y:
                grounding['normal'] = n
                grounding['penetration'] = -arbiter.contacts[0].distance
                grounding['body'] = arbiter.shapes[1].body
                grounding['impulse'] = arbiter.total_impulse
                grounding['position'] = arbiter.contacts[0].position
        self.body.each_arbiter(f)
        self.well_grounded = False
        if grounding['body'] != None and abs(grounding['normal'].x/grounding['normal'].y) < self.feet.friction:
            self.well_grounded = True
            self.remaining_jumps = 2
    
        self.ground_velocity = Vec2d.zero()
        if self.well_grounded:
            self.ground_velocity = grounding['body'].velocity
            
        self.target_vx = 0
        if self.body.velocity.x > .01:
            self.direction = 1
        elif self.body.velocity.x < -.01:
            self.direction = -1
        if self.kb_handler[pyglet.window.key.LEFT]:
            self.direction = -1
            self.target_vx -= PLAYER_VELOCITY
        if self.kb_handler[pyglet.window.key.RIGHT]:
            self.direction = 1
            self.target_vx += PLAYER_VELOCITY
        if self.kb_handler[pyglet.window.key.DOWN]:
            self.direction = -3    
        self.feet.surface_velocity = self.target_vx, 0

        if grounding['body'] != None:
            self.feet.friction = -PLAYER_GROUND_ACCEL/self.space.gravity.y #IGNORE:E1101
            self.head.friciton = HEAD_FRICTION
        else:
            self.feet.friction, self.head.friction = 0, 0
        # Air control
        if grounding['body'] == None:
            self.body.velocity.x = cpflerpconst(self.body.velocity.x, self.target_vx + self.ground_velocity.x, PLAYER_AIR_ACCEL * DT)
        self.body.velocity.y = max(self.body.velocity.y, -FALL_VELOCITY) # clamp upwards as well?
        
        # Move the moving platform
        destination = self.space.platform_path[self.space.platform_path_index]
        current = Vec2d(self.space.platform_body.position)
        distance = current.get_distance(destination)
        if distance < PLATFORM_SPEED:
            self.space.platform_path_index += 1
            self.space.platform_path_index = self.space.platform_path_index % len(self.space.platform_path)
            t = 1
        else:
            t = PLATFORM_SPEED / distance
        new = current.interpolate_to(destination, t)
        self.space.platform_body.position = new
        self.space.platform_body.velocity = (new - current) / DT
            
        # Did we land?
        if abs(grounding['impulse'].y) / self.body.mass > 200 and not self.landed_previous:
            #sound.play()
            self.landing = {'p':grounding['position'],'n':5}
            self.landed_previous = True
        else:
            self.landed_previous = False
        if self.landing['n'] > 0:
            #pygame.draw.circle(screen, pygame.color.THECOLORS['yellow'], to_pygame(landing['p'], screen), 5)
            self.landing['n'] -= 1

    def main(self):
        fps = pyglet.clock.ClockDisplay(clock=self.clock)
        frame_number = 0
        while True:
            self.dispatch_events()
            self.movement()
            # Drawing
            self.clear()
            self.draw_lines()
            self.batch.draw()    
            fps.draw()
            self.space.step(1/50.0)
            self.clock.tick(50)
            self.flip()

if __name__ == '__main__':
    TEST = Main()
    TEST.main()