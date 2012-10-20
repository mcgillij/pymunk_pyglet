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
        self.start_line = None
        
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
        
    def on_mouse_release(self, x, y, button, modifiers):
        if not (x, y) == self.start_line:
            print "adding line"
            s = pymunk.Segment(self.space.static_body, self.start_line, (x, y), 5)
            self.space.add(s)

    def on_key_press(self, k, m):
        if k == pyglet.window.key.ESCAPE:
            sys.exit()
        elif k == pyglet.window.key.S:
            # saving 
            self.space.save()
        elif k == pyglet.window.key.L:
            # loading
            self.space.load()
        
    def on_key_release(self, k, m):
        pass
    
    def draw_lines(self):
        self.batch = pyglet.graphics.Batch()
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
                self.batch.add(len(ps), GL_LINE_STRIP, None,
                         ('v2f', xs),
                          ('c4f', (0.0, 0.0, 1.0, 1.0) * len(ps)))

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

if __name__ == '__main__':
    TEST = Main()
    TEST.main()