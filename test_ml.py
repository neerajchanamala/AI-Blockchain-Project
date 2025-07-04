import unittest
from ml import extract_text_from_image, check_harmful

class TestMLModel(unittest.TestCase):
    def test_text_extraction(self):
        text = extract_text_from_image("sample_image.jpg")  # Replace with a real image path
        self.assertTrue(len(text) > 0, "OCR should extract some text.")

    def test_harmful_detection(self):
        ingredients = ["sodium benzoate", "sugar", "trans fat"]
        result = check_harmful(ingredients)
        self.assertIn("sodium benzoate", result, "Should detect harmful ingredient.")
        self.assertIn("trans fat", result, "Should detect harmful ingredient.")
        self.assertNotIn("sugar", result, "Sugar is not harmful in the dataset.")

if __name__ == '__main__':
    unittest.main()
