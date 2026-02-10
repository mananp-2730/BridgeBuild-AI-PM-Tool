import unittest
from utils import convert_currency

class TestUtils(unittest.TestCase):
    
    def test_currency_conversion_usd(self):
        # Test basic USD formatting
        self.assertEqual(convert_currency("5000", "USD ($)"), "$5,000")
        
    def test_currency_conversion_inr(self):
        # Test USD to INR conversion (approx 85x)
        self.assertEqual(convert_currency("100", "INR (₹)"), "₹8,500")

    def test_invalid_input(self):
        # Test graceful failure
        self.assertEqual(convert_currency("invalid", "USD ($)"), "invalid")

if __name__ == '__main__':
    unittest.main()