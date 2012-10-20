import pymunk
import pickle
import level

class World(pymunk.Space):
    def __init__(self):
        super(World, self).__init__()
        self.gravity = 0, -1000
        # moving platform
        self.platform_path = [(650,100),(600,200),(650,300)]
        self.platform_path_index = 0
        self.platform_body = pymunk.Body(pymunk.inf, pymunk.inf)
        self.platform_body.position = 650,100
        s = pymunk.Segment(self.platform_body, (-25, 0), (25, 0), 5)
        s.friction = 1.
        s.group = 1
        self.add(s)
        
        # pass through platform
        passthrough = pymunk.Segment(self.static_body, (270, 100), (320, 100), 5)
        passthrough.friction = 1.
        passthrough.collision_type = 2
        passthrough.layers = passthrough.layers ^ 0b1000
        self.add(passthrough)
        
    def save(self):
        lvl = level.Level()
        for shape in self.shapes:
            if  isinstance(shape, pymunk.Segment):
                body = shape.body
                pv1 = body.position + shape.a.rotated(body.angle)
                pv2 = body.position + shape.b.rotated(body.angle)
                lvl.segments.append([pv1.x, pv1.y, pv2.x, pv2.y])
                
            elif isinstance(shape, pymunk.Poly):
                ps = shape.get_points()
                ps = [ps[0]] + ps + [ps[0], ps[0]]
                xs = []
                for p in ps:
                    xs.append(p.x)
                    xs.append(p.y)
                lvl.polys.append([xs])
                                      
            elif isinstance(shape, pymunk.Circle):
                p = shape.body.position
                ps = [p + (0,shape.radius), p + (shape.radius,0),
                        p + (0,-shape.radius), p + (-shape.radius,0)]
                ps += [ps[0]]
                xs = []
                for p in ps:
                    xs.append(p.x)
                    xs.append(p.y)
                lvl.circles.append([xs])
                
        output_file = open('level.pkl', 'wb')
        pickle.dump(lvl, output_file)
        output_file.close()
        
    def load(self):
        input_file = open('level.pkl', 'rb')
        lvl = pickle.load(input_file)
        segments = []
        for seg in lvl.segments:
            s = pymunk.Segment(self.static_body, (seg[0], seg[1]), (seg[2], seg[3]), 5)
            s.friction = 1.
            s.group = 1
            segments.append(s)
        self.add(segments)        
        input_file.close()
        
    def basic_world(self):
        static = [
            pymunk.Segment(self.static_body, (10, 50), (300, 50), 5)
            , pymunk.Segment(self.static_body, (300, 50), (325, 50), 5)
            , pymunk.Segment(self.static_body, (325, 50), (350, 50), 5)
            , pymunk.Segment(self.static_body, (350, 50), (375, 50), 5)
            , pymunk.Segment(self.static_body, (375, 50), (680, 50), 5)
            , pymunk.Segment(self.static_body, (680, 50), (680, 370), 5)
            , pymunk.Segment(self.static_body, (680, 370), (10, 370), 5)
            , pymunk.Segment(self.static_body, (10, 370), (10, 50), 5)
                ]  
        # rounded shape
        rounded = [
                pymunk.Segment(self.static_body, (500, 50), (520, 60), 5)
            , pymunk.Segment(self.static_body, (520, 60), (540, 80), 5)
            , pymunk.Segment(self.static_body, (540, 80), (550, 100), 5)
            , pymunk.Segment(self.static_body, (550, 100), (550, 150), 5)
                    ]
        # static platforms
        platforms = [
                  pymunk.Segment(self.static_body, (170, 50), (270, 150), 5)
            #, pymunk.Segment(space.static_body, (270, 100), (300, 100), 5)
            , pymunk.Segment(self.static_body, (400, 150), (450, 150), 5)
            , pymunk.Segment(self.static_body, (400, 200), (450, 200), 5)
            , pymunk.Segment(self.static_body, (220, 200), (300, 200), 5)
            , pymunk.Segment(self.static_body, (50, 250), (200, 250), 5)
            , pymunk.Segment(self.static_body, (10, 370), (50, 250), 5)
                    ]
        for s in static + platforms + rounded:
            s.friction = 1.
            s.group = 1

        self.add(static, platforms + rounded)
        
        