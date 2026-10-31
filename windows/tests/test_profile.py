"""Offline tests for Windows GeneRev4 profile format."""
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gene_profile import EXAMPLE, ProfilePoint, export_csv, export_txt, parse_profile, target_at, mmss


class ProfileTests(unittest.TestCase):
    def test_nico_csv_with_sentinel(self):
        pts = parse_profile("999;title\n0;180\n60;195,5\n120;210\n")
        self.assertEqual(pts[1], ProfilePoint(60, 195.5))
        self.assertEqual(target_at(pts, 59), 180)
        self.assertEqual(target_at(pts, 60), 195.5)

    def test_txt_tn_Tn_pairs(self):
        pts = parse_profile("[t1=0]\n[T1=180]\n[t2=60]\n[T2=200]")
        self.assertEqual(pts, [ProfilePoint(0,180), ProfilePoint(60,200)])

    def test_roundtrip_csv_and_txt(self):
        self.assertEqual(EXAMPLE, parse_profile(export_csv(EXAMPLE)))
        self.assertEqual(EXAMPLE, parse_profile(export_txt(EXAMPLE)))

    def test_invalid_data(self):
        for content in (
            "", "-1;180", "0;140", "0;280", "2;180\n1;190",
            "0;180\n0;190", "0;not_a_number", "[t1=0]",
            "[t1=0]\n[T2=180]", "0.5;180", "30000;190"
        ):
            with self.subTest(profile=content), self.assertRaises(ValueError):
                parse_profile(content)

    def test_clock(self):
        self.assertEqual(mmss(125), "02:05")


if __name__=="__main__":
    unittest.main()
