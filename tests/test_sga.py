import unittest
from sga import TlSga
from controller import Controller

class TestSgaTl(unittest.TestCase):

    def setUp(self):
        self.ctrl = Controller()
        self.sga = TlSga(controller=self.ctrl)

    def test_controller_is_assigned(self):
        """Verifica que el controlador se asigne correctamente"""
        self.assertIsNotNone(self.sga.controller)

    def test_run_generation_returns_dict(self):
        """Valida que run_generation devuelva un dict con fitness"""
        result = self.sga.run_generation()
        self.assertIsInstance(result, dict)
        self.assertIn("best_fitness", result)
        self.assertIn("avg_fitness", result)
