import unittest

from DaskPool import DaskPool


class DaskPoolTestCase(unittest.TestCase):
    def setUp(self):
        self.daskPool = DaskPool()

    def test_maintain_pool(self):
        self.assertEqual(len(self.daskPool.instances), 0)
        self.daskPool.maintain_pool()
        self.assertEqual(len(self.daskPool.instances), self.daskPool.target_count)

        self.daskPool.maintain_pool()
        self.assertEqual(len(self.daskPool.instances), self.daskPool.target_count)

    def test_add_to_pool(self):
        self.daskPool.maintain_pool()

        self.daskPool.add_to_pool(1)
        self.assertEqual(len(self.daskPool.instances), self.daskPool.target_count + 1)

        self.daskPool.maintain_pool()
        self.assertEqual(len(self.daskPool.instances), self.daskPool.target_count)

    def test_remove_from_pool(self):
        self.daskPool.maintain_pool()

        self.daskPool.remove_from_pool(1)
        self.assertEqual(len(self.daskPool.instances), self.daskPool.target_count - 1)

        self.daskPool.maintain_pool()
        self.assertEqual(len(self.daskPool.instances), self.daskPool.target_count)

    def test_restart_pool(self):
        self.daskPool.maintain_pool()

        ip_a = set([i.ip_address for i in self.daskPool.instances])
        self.daskPool.restart_pool()
        ip_b = set([i.ip_address for i in self.daskPool.instances])
        self.assertEqual(len(ip_a.intersection(ip_b)), 0)

    def test_terminate_pool(self):
        self.daskPool.maintain_pool()

        self.daskPool.terminate_pool()
        self.assertEqual(len(self.daskPool.instances), 0)

    def tearDown(self):
        self.daskPool.terminate_pool()


if __name__ == "__main__":
    unittest.main()
