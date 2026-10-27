"""Compare every directional key pair with the user's two reference screenshots."""
import unittest
from pathlib import Path

from faderlogic import camelot


class ScreenshotChartTests(unittest.TestCase):
    def tearDown(self):
        camelot.set_active_chart(next(iter(camelot.CHART_CHOICES)))

    def test_all_chart_cells_and_all_unlisted_pairs(self):
        columns = [
            [("perfect", "Perfect Match"), ("boost_1", "Energy Boost (+)"),
             ("boost_2", "Energy Boost (++)"), ("boost_3", "Energy Boost (+++)"),
             ("drop_1", "Energy Drop (-)"), ("drop_2", "Energy Drop (--)"),
             ("drop_3", "Energy Drop (---)"), ("mood", "Mood Change")],
            [("perfect", "Perfect Mix"), ("minus1", "-1 Mix"), ("plus1", "+1 Mix"),
             ("boost", "Energy Boost"), ("scale", "Scale Change"),
             ("diagonal", "Diagonal Mix"), ("jaw", "Jaw's Mix"), ("mood", "Mood Shifter")],
        ]
        keys = {f"{n}{letter}" for n in range(1, 13) for letter in "AB"}
        for number, name in enumerate(camelot.CHART_CHOICES, 1):
            camelot.set_active_chart(name)
            fixture = Path(__file__).parent / "fixtures" / f"chart{number}.txt"
            rows = [line.split("|") for line in fixture.read_text().splitlines()
                    if line and not line.startswith("#")]
            self.assertEqual({row[0] for row in rows}, keys)
            for start, *cells in rows:
                expected = {}
                for (category, label), cell in zip(columns[number - 1], cells, strict=True):
                    with self.subTest(chart=number, key=start, column=category):
                        self.assertEqual(camelot.CHART_CHOICES[name][start][category], cell.split())
                    for destination in cell.split():
                        self.assertNotIn(destination, expected)
                        expected[destination] = label
                for destination in keys:
                    with self.subTest(chart=number, start=start, destination=destination):
                        self.assertEqual(camelot.get_compatibility(start, destination)[1],
                                         expected.get(destination, "Incompatible"))

    def test_chart_one_direction_is_not_reversed(self):
        camelot.set_active_chart(next(iter(camelot.CHART_CHOICES)))
        self.assertEqual(camelot.get_compatibility("8A", "8B")[1], "Energy Boost (+)")
        self.assertEqual(camelot.get_compatibility("8B", "8A")[1], "Energy Drop (-)")


if __name__ == "__main__":
    unittest.main()
