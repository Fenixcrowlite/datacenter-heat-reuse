"""Bounded independent tests for the v87 renewal prototype."""
import unittest
from dataclasses import replace
from decimal import Decimal
from prototype_renewable_cap_v87 import Raw, Retained, D, renew, verify

def raw():
    return Raw(D(4),D(1),D(0.5),D(2),D(12),D(5),D(7),D(1),D('0.92'))
def memory():
    return Retained(0,D(0),D(1),'HP_ON',D(1),D(0),D(0),D(0),D(0),'event-hull-v86')
KEY=b'local-test-key-not-a-production-secret'
def issue(r=None,m=None,h=None,prev=None):
    return renew(r or raw(),m or memory(),h or D(1),'study-dchr',KEY,previous=prev)

class RenewableCapTest(unittest.TestCase):
    def test_authentic_certificate(self):
        c=issue()
        self.assertTrue(verify(c,raw(),KEY))
        self.assertEqual(c.schema,1)
        self.assertEqual(c.generation,1)
    def test_inventory_bound_and_compressor_rating(self):
        r=raw();c=issue()
        inventory=D(c.inventory_bound)
        self.assertGreaterEqual(inventory,memory().inventory_upper)
        L=max(r.floor,r.b+inventory/r.C)
        work=D(c.effective_heat_cap)*L/(r.A+L)
        self.assertLessEqual(work,r.p_max)
    def test_monotonic_horizon(self):
        caps=[D(issue(h=D(x)).effective_heat_cap) for x in (1,2,4,8)]
        self.assertEqual(caps,sorted(caps,reverse=True))
    def test_charging_saturates_at_capacity(self):
        c=issue(h=D(100))
        self.assertEqual(D(c.inventory_bound),raw().capacity)
    def test_renewal_preserves_memory_provenance(self):
        initial=memory();c=issue()
        self.assertEqual(initial.latch,'HP_ON')
        self.assertEqual(initial.on_age,D(1))
        after=replace(initial,generation=c.generation,clock_upper=D(c.expiry_upper),
                      inventory_upper=D(c.inventory_bound))
        next_cert=issue(m=after,prev=c,h=D('0.5'))
        self.assertEqual(next_cert.generation,2)
        self.assertEqual(next_cert.clock_start_upper,c.expiry_upper)
    def test_early_renewal_refused(self):
        c=issue()
        middle=replace(memory(),generation=c.generation,clock_upper=D('0.25'))
        with self.assertRaisesRegex(ValueError,'early renewal'):
            issue(m=middle,prev=c)
    def test_wrong_generation_refused(self):
        c=issue();m=replace(memory(),clock_upper=D(c.expiry_upper))
        with self.assertRaisesRegex(ValueError,'generation mismatch'):
            issue(m=m,prev=c)
    def test_tamper_refused(self):
        c=issue()
        with self.assertRaisesRegex(ValueError,'unauthenticated'):
            verify(replace(c, effective_heat_cap='999'),raw(),KEY)
    def test_raw_policy_change_refused(self):
        c=issue();new=replace(raw(),p_max=D('1.1'))
        with self.assertRaisesRegex(ValueError,'raw policy changed'):
            verify(c,new,KEY)
    def test_zero_rating(self):
        r=replace(raw(),p_max=D(0))
        self.assertEqual(D(issue(r=r).effective_heat_cap),D(0))
    def test_nonbinding_compressor(self):
        r=replace(raw(),p_max=D(999))
        self.assertEqual(D(issue(r=r).effective_heat_cap),r.thermal_cap)
    def test_initial_inventory_over_capacity(self):
        r=replace(raw(),capacity=D('0.5'))
        with self.assertRaisesRegex(ValueError,'inventory'):
            issue(r=r)
    def test_negative_expiry(self):
        with self.assertRaises(ValueError):
            issue(h=D(-1))
    def test_wrong_origin(self):
        c=issue();m=replace(memory(),generation=1,clock_upper=D(c.expiry_upper))
        with self.assertRaisesRegex(ValueError,'origin'):
            renew(raw(),m,D(1),'different-origin',KEY,c)

if __name__=='__main__':
    unittest.main(verbosity=2)
