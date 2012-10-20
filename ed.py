#IGNORE:C0301
import sys, math
import pyglet
from pyglet.gl import *
import pymunk
from pymunk.vec2d import Vec2d
import world
import pickle
import level

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
        self.space = world.World()
        self.space.load()
        self.start_line = None
        self.polys = []
        self.poly_points = []
        self.balls = []
        
        def passthrough_handler(space, arbiter):
            if arbiter.shapes[0].body.velocity.y < 0:
                return True
            else:
                return False
                
        self.space.add_collision_handler(1,2, begin=passthrough_handler)
        # player

    def on_mouse_press(self, x, y, button, modifiers ):
        #pymunk.Segment(self.space.static_body, (10, 50), (300, 50), 5)
        self.start_line = (x, y)
        if button == 4: #right mouse button
            p = Vec2d(x, y)
            self.poly_points.append(p)
    def on_mouse_motion(self, x, y, button, modifiers):
        if button == 4: #right mouse button
            p = Vec2d(x, y)
            self.poly_points.append(p)
            
        
    def on_mouse_release(self, x, y, button, modifiers):
        #p = Vec2d(x, y)
        #self.balls.append(self.create_ball(p))
        if not (x, y) == self.start_line:
            self.create_wall(x, y, self.start_line[0], self.start_line[1])
        if button == 4:
            print "adding poly?"
            if len(self.poly_points) > 0:
                self.poly_points = pymunk.util.reduce_poly(self.poly_points, tolerance=5)
            if len(self.poly_points) > 2:
                self.poly_points = pymunk.util.convex_hull(self.poly_points)
                if not pymunk.util.is_clockwise(self.poly_points):
                    self.poly_points.reverse()
                    
                center = pymunk.util.calc_center(self.poly_points)
                self.poly_points = pymunk.util.poly_vectors_around_center(self.poly_points)
                self.polys.append(self.create_poly(self.poly_points, pos=center))
            self.poly_points = []
            
    def on_key_press(self, k, m):
        if k == pyglet.window.key.ESCAPE:
            sys.exit()
        elif k == pyglet.window.key.K:
            #spawn a bunch of boxes
            self.make_a_bunch_of_boxes()
        elif k == pyglet.window.key.S:
            # saving 
            self.space.save()
        elif k == pyglet.window.key.L:
            # loading
            self.space.load()
        
    def on_key_release(self, k, m):
        pass
    
    def make_a_bunch_of_boxes(self):
        for x in range (-100,100,25):
            for y in range(-100,100,25):
                p = self.start_line
                self.polys.append(self.create_box(pos=p))          
    
    def create_wall(self, x, y, x2, y2):
        print "adding line"
        s = pymunk.Segment(self.space.static_body, self.start_line, (x, y), 5)
        self.space.add(s)

    def create_ball(self, point, mass=1.0, radius=15.0):
        moment = pymunk.moment_for_circle(mass, radius, 0.0, Vec2d(0,0))
        ball_body = pymunk.Body(mass, moment)
        ball_body.position = Vec2d(point)
                
        ball_shape = pymunk.Circle(ball_body, radius, Vec2d(0,0))
        ball_shape.friction = 1.5
        ball_shape.collision_type = 1
        self.space.add(ball_body, ball_shape)
        return ball_shape
    
    def create_box(self, pos, size = 10, mass = 5.0):
        box_points = map(Vec2d, [(-size, -size), (-size, size), (size,size), (size, -size)])
        return self.create_poly(box_points, mass = mass, pos = pos)

    def create_poly(self, points, mass = 5.0, pos = (0,0)):
        moment = pymunk.moment_for_poly(mass,points, Vec2d(0,0))    
        #moment = 1000
        body = pymunk.Body(mass, moment)
        body.position = Vec2d(pos)       
        print body.position
        shape = pymunk.Poly(body, points, Vec2d(0,0))
        shape.friction = 0.5
        shape.collision_type = 1
        self.space.add(body, shape)
        return shape
    
    def draw_lines(self):
        self.batch = pyglet.graphics.Batch()
        if len(self.poly_points) > 1:
            ps = [Vec2d(p) for p in self.poly_points]
            x, y = ps[0]
            xx, yy = ps[1]

            self.batch.add(2, GL_LINES, None, 
                    ('v2f', (x, y, xx, yy) ),
                     ('c4f', (0.0, 1.0, 0.0, 1.0) * 2))
      
        for shape in self.space.shapes:
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
                #print str(ps)
                #print str(xs)
                self.batch.add(len(ps), GL_LINE_STRIP, None,
                         ('v2f', xs),
                          ('c4f', (0.0, 0.0, 1.0, 1.0) * len(ps)))
                
    def remove_balls(self):
        xs = []
        for ball in self.balls:
            if ball.body.position.x < -1000 or ball.body.position.x > 1000 \
                or ball.body.position.y < -1000 or ball.body.position.y > 1000:
                xs.append(ball)
        for ball in xs:
            self.space.remove(ball, ball.body)
            self.balls.remove(ball)
                
    def remove_polys(self):
        # Polys
        xs = []
        for poly in self.polys:
            if poly.body.position.x < -1000 or poly.body.position.x > 1000 \
                or poly.body.position.y < -1000 or poly.body.position.y > 1000:
                xs.append(poly)
        
        for poly in xs:
            self.space.remove(poly, poly.body)
            self.polys.remove(poly)

    def main(self):
        fps = pyglet.clock.ClockDisplay(clock=self.clock)
        while True:
            self.dispatch_events()
            # Drawing
            self.clear()
            self.draw_lines()
            self.batch.draw()    
            fps.draw()
            self.space.step(1/50.0)
            self.clock.tick(50)
            self.flip()
            self.remove_polys()
            self.remove_balls()

if __name__ == '__main__':
    TEST = Main()
    TEST.main()