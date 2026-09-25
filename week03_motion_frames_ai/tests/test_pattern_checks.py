import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'ros2_ws/src/week03_pattern'))
from week03_pattern.pattern import Segment
from week03_pattern.checks import validate,shape_ok,command_at,endpoint


class PatternCheckTests(unittest.TestCase):
    def test_specified_shapes_and_wrong_order(self):
        l=[Segment(.1,0,4),Segment(0,.5,math.pi),Segment(.1,0,4)]
        self.assertTrue(shape_ok('l_path',l))
        self.assertFalse(shape_ok('l_path',[l[1],l[0],l[2]]))
        rectangle=[]
        for distance in (.4,.25,.4,.25):
            rectangle.extend([Segment(.1,0,distance/.1),Segment(.075,.5,math.pi)])
        self.assertTrue(shape_ok('rounded_rectangle',rectangle))
        self.assertAlmostEqual(endpoint(rectangle)['x'],0)
        arcs=[Segment(.15,w,math.pi/2) for w in (.5,-.5,.5,-.5)]
        self.assertTrue(shape_ok('alternating_arcs',arcs))
        arcs[1]=arcs[0]
        self.assertFalse(shape_ok('alternating_arcs',arcs))

    def test_reject_nonfinite_empty_and_unbounded(self):
        for segments in ([],[Segment(float('nan'),0,1)],[Segment(.3,0,1)], [Segment(0,0,-1)], [Segment(.1,0,30)]*3):
            with self.assertRaises(ValueError): validate(segments)

    def test_stop_at_boundary_and_empty(self):
        segments=[Segment(.1,0,2),Segment(0,.5,1)]
        self.assertEqual(command_at(segments,1.99),(.1,0))
        self.assertEqual(command_at(segments,2),(0,.5))
        self.assertEqual(command_at(segments,3),(0,0))
        self.assertEqual(command_at([],0),(0,0))

    def test_stop_at_fractional_total_despite_rounding(self):
        arc_duration=(math.pi/2)/.8
        segments=[]
        for distance in (.4,.25,.4,.25):
            segments.extend((Segment(.2,0,distance/.2),Segment(.12,.8,arc_duration)))
        total=sum(segment.duration for segment in segments)
        self.assertEqual(command_at(segments,total-1e-6),(.12,.8))
        self.assertEqual(command_at(segments,total),(0.,0.))
        self.assertEqual(command_at(segments,total+1e-6),(0.,0.))
