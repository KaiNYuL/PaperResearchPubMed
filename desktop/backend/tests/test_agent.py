import unittest

from app.agent import parse_user_query


class AgentParseTests(unittest.TestCase):
    def test_parse_year_range(self):
        result = parse_user_query("2021-2023 年 糖尿病 机器学习")
        self.assertEqual(result["start_year"], 2021)
        self.assertEqual(result["end_year"], 2023)

    def test_parse_keywords(self):
        result = parse_user_query("2024 糖尿病 机器学习 治疗")
        self.assertIn("糖尿病", result["keywords"])
        self.assertIn("机器学习", result["keywords"])


if __name__ == "__main__":
    unittest.main()
