import unittest
from controller import Controller

class TestController(unittest.TestCase):

    def setUp(self):
        """Corre antes de cada test"""
        self.ctrl = Controller(config="test.sumo.cfg", use_ui=False, port=9999)

    def test_initialization(self):
        """Verifica que los parámetros se inicialicen correctamente"""
        self.assertEqual(self.ctrl.config, "test.sumo.cfg")
        self.assertFalse(self.ctrl.use_ui)
        self.assertEqual(self.ctrl.port, 9999)

    def test_connect_returns_true(self):
        """Simula conexión exitosa"""
        self.assertTrue(self.ctrl.connect())

    def test_get_sumo_binary_returns_path(self):
        """Valida que el path del binario sea válido"""
        path = self.ctrl.get_sumo_binary()
        self.assertIn("sumo.exe", path)
