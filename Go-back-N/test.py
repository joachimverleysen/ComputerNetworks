# Basic example of testing a module with the "unitest" library

import unittest

class Calculations():
    def __init__(self, a, b):
        self.a = a
        self.b = b
        
    def get_sum(self):
        return self.a + self.b

    def get_difference(self):
        return self.a - self.b
        
    def get_product(self):
        return self.a * self.b
        
    def get_quotient(self):
        return self.a / self.b

class TestCalculations(unittest.TestCase):
    def test_sum(self):
        calculation = Calculations(4, 5)
        self.assertEqual(calculation.get_sum(), 9)


if __name__ == "__main__":
    unittest.main()

