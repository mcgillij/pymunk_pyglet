import sys, random
import pyglet
import pymunk

pyglet.options['debug_gl'] = False

class PygApp(pyglet.window.Window):
    is_event_handler = True
    def __init__(self, *args, **kwargs):
        platform = pyglet.window.get_platform()
        display = platform.get_default_display()
        screen = display.get_default_screen()
        template = pyglet.gl.Config(double_buffer=True)
        config = screen.get_best_config(template)
        context = config.create_context(None)
        super(PygApp, self).__init__(resizable=True, width=800, height=600, caption="pymunk test" , context=context)
        self.space = pymunk.Space()
        self.space.gravity = (0.0, -900.0)
        self.ball_sprite = pyglet.sprite.Sprite(pyglet.image.load('bit.png'))
        self.clock = pyglet.clock.Clock()
        self.ticks_to_next_ball = 10
        self.balls = []
        self.lines = self.add_L()

    def add_ball(self):
        """Add a ball to the given space at a random position"""
        mass = 1
        radius = 14
        inertia = pymunk.moment_for_circle(mass, 0, radius, (0,0))
        body = pymunk.Body(mass, inertia)
        x = random.randint(120,380)
        body.position = x, 550
        shape = pymunk.Circle(body, radius, (0,0))
        self.space.add(body, shape)
        return shape

    def draw_ball(self, ball):
        """Draw a ball shape"""
        self.ball_sprite.position = int(ball.body.position.x), int(ball.body.position.y)
        self.ball_sprite.draw()
    
    def add_L(self):
        """Add a inverted L shape with two joints"""
        rotation_center_body = pymunk.Body()
        rotation_center_body.position = (300,300)
        rotation_limit_body = pymunk.Body() # 1
        rotation_limit_body.position = (200,300)
        body = pymunk.Body(10, 10000)
        body.position = (300,300)    
        l1 = pymunk.Segment(body, (-150, 0), (255.0, 0.0), 5.0)
        l2 = pymunk.Segment(body, (-150.0, 0), (-150.0, 50.0), 5.0)
        rotation_center_joint = pymunk.PinJoint(body, rotation_center_body, (0,0), (0,0)) 
        joint_limit = 25
        rotation_limit_joint = pymunk.SlideJoint(body, rotation_limit_body, (-100,0), (0,0), 0, joint_limit) # 3
        self.space.add(l1, l2, body, rotation_center_joint, rotation_limit_joint)
        return l1,l2

    def draw_lines(self):
        """Draw the lines"""
        for line in self.lines:
            body = line.body
            pv1 = body.position + line.a.rotated(body.angle)
            pv2 = body.position + line.b.rotated(body.angle)
            pyglet.graphics.draw(2, pyglet.gl.GL_LINES, ('v2f', (pv1.x, pv1.y, pv2.x, pv2.y)))

    def on_key_press(self, k, m):
        if k == pyglet.window.key.ESCAPE:
            sys.exit()

    def main(self):
        fps = pyglet.clock.ClockDisplay(clock=self.clock)
        while True:
            self.dispatch_events()
            self.ticks_to_next_ball -= 1
            if self.ticks_to_next_ball <= 0:
                self.ticks_to_next_ball = 25
                ball_shape = self.add_ball()
                self.balls.append(ball_shape)
            self.clear()
            balls_to_remove = []
            for ball in self.balls:
                if ball.body.position.y < 150:
                    balls_to_remove.append(ball)
                self.draw_ball(ball)
            for ball in balls_to_remove:
                self.space.remove(ball, ball.body)
                self.balls.remove(ball)
            self.draw_lines()
            fps.draw()
            self.space.step(1/50.0)
            self.clock.tick(50)
            self.flip()

if __name__ == '__main__':
    TEST = PygApp()
    TEST.main()