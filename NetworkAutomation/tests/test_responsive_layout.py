import unittest
from modules.responsive_layout import SidebarPolicy,flow_positions

class ResponsiveTests(unittest.TestCase):
    def test_wide_toolbar_one_row(self):
        self.assertEqual(flow_positions(800,[140,90,170,90]),[(0,0),(0,1),(0,2),(0,3)])
    def test_narrow_toolbar_wraps(self):
        self.assertEqual(flow_positions(300,[140,90,170,90]),[(0,0),(0,1),(1,0),(1,1)])
    def test_large_dpi_widgets_wrap(self):
        self.assertEqual(flow_positions(600,[280,180,340,180]),[(0,0),(0,1),(1,0),(1,1)])
    def test_zero_width_no_crash(self):
        self.assertEqual(flow_positions(0,[100,200]),[(0,0),(1,0)])
    def test_sidebar_preserves_manual_choice_until_breakpoint_change(self):
        policy=SidebarPolicy()
        self.assertFalse(policy.resize(1000));self.assertTrue(policy.toggle())
        self.assertTrue(policy.resize(1010));self.assertTrue(policy.resize(1400))
        self.assertFalse(policy.toggle());self.assertFalse(policy.resize(1450))
        self.assertFalse(policy.resize(1000))
    def test_multiple_wraps_keep_every_widget(self):
        sizes=[50,100,200,90,80,160]
        positions=flow_positions(220,sizes)
        self.assertEqual(len(positions),len(sizes))
        self.assertGreater(max(x[0] for x in positions),1)

if __name__=='__main__':unittest.main()
