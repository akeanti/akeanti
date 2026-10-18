"""Offline tests for the profile builder: no network, no token.

    python3 -m unittest discover -s .github/tests -v
"""
import argparse
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from xml.etree import ElementTree

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(REPO, ".github", "scripts"))
import build_profile as bp  # noqa: E402

FIXTURE = os.path.join(HERE, "fixture.json")
SVG = "{http://www.w3.org/2000/svg}"


def no_network(url, *args, **kwargs):
    raise OSError(f"no network in the tests: {url}")


class Sandbox(unittest.TestCase):
    """The profile copied into a temporary directory, with the builder pointed at it and the network cut."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        for path in ("README.md", "assets", "cv", ".github/data", ".github/scripts", ".github/workflows"):
            src, dst = os.path.join(REPO, path), os.path.join(self.tmp, path)
            if os.path.isdir(src):
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "github.json"))
            else:
                shutil.copy(src, dst)
        self.saved = {k: getattr(bp, k) for k in ("ROOT", "ASSETS", "README", "DATA", "SNAPSHOT", "http")}
        bp.ROOT, bp.ASSETS, bp.README = self.tmp, os.path.join(self.tmp, "assets"), os.path.join(self.tmp, "README.md")
        bp.DATA = os.path.join(self.tmp, ".github", "data")
        bp.SNAPSHOT = os.path.join(bp.DATA, "github.json")
        bp.http = no_network
        bp.CHANGED.clear()
        bp.WARNINGS.clear()
        with open(FIXTURE, encoding="utf8") as fh:
            self.user = json.load(fh)

    def tearDown(self):
        for k, v in self.saved.items():
            setattr(bp, k, v)
        shutil.rmtree(self.tmp)

    def build(self):
        with contextlib.redirect_stdout(io.StringIO()):
            return bp.build(self.user, offline=True)

    def readme(self):
        with open(bp.README, encoding="utf8") as fh:
            return fh.read()

    def svgs(self):
        return {n: ElementTree.parse(os.path.join(bp.ASSETS, n)).getroot()
                for n in sorted(os.listdir(bp.ASSETS)) if n.endswith(".svg")}


class BuildTest(Sandbox):
    def test_a_build_passes_every_check_without_warnings(self):
        self.build()
        self.assertEqual(bp.check(), [])
        self.assertEqual(bp.WARNINGS, [])

    def test_every_graphic_is_valid_and_has_a_title(self):
        self.build()
        for name, root in self.svgs().items():
            with self.subTest(name):
                self.assertIsNotNone(root.find(f"{SVG}title"), "screen readers announce the title")
                self.assertTrue(root.get("viewBox"), "without a viewBox it does not scale")

    def test_a_second_build_changes_nothing(self):
        self.build()
        bp.CHANGED.clear()
        self.build()
        self.assertEqual(bp.CHANGED, [], "the workflow would commit on every run")

    def test_the_data_behind_the_graphics_is_kept(self):
        self.build()
        with open(bp.SNAPSHOT, encoding="utf8") as fh:
            self.assertEqual(json.load(fh), self.user)

    def test_a_failed_fetch_rebuilds_from_the_snapshot(self):
        self.build()
        os.environ.setdefault("GITHUB_TOKEN", "unused")
        with contextlib.redirect_stdout(io.StringIO()):
            user = bp.github(argparse.Namespace(data=None, save=None))
        self.assertEqual(user, self.user)
        self.assertTrue(any("snapshot" in w for w in bp.WARNINGS))

    def test_stale_graphics_are_removed(self):
        with open(os.path.join(bp.ASSETS, "kpis-old.svg"), "w", encoding="utf8") as fh:
            fh.write('<svg xmlns="http://www.w3.org/2000/svg"/>')
        self.build()
        self.assertFalse(os.path.exists(os.path.join(bp.ASSETS, "kpis-old.svg")))
        self.assertIn("assets/kpis-old.svg (removed)", bp.CHANGED)

    def test_the_generated_blocks_carry_links_contact_and_every_pin(self):
        self.build()
        text = self.readme()
        for k in bp.KPIS:
            self.assertIn(f'href="{k["proof"]}"', text)
        self.assertIn('<a name="proof"></a>', text)
        for pin in self.user["pinnedItems"]["nodes"]:
            self.assertIn(pin["url"], text)
        self.assertIn(bp.EMAIL, text.split("TEXT:START")[1])
        self.assertIn("akeanti.xyz/ariadne", text)

    def test_animations_have_one_value_per_key_time(self):
        self.build()
        svgs = self.svgs()
        for name in ("live-race.svg", "live-spell.svg"):
            for el in svgs[name].iter():
                if el.get("keyTimes") is None:
                    continue
                keys = [float(k) for k in el.get("keyTimes").split(";")]
                values = (el.get("values") or el.get("keyPoints")).split(";")
                with self.subTest(name, tag=el.tag):
                    self.assertEqual(len(keys), len(values))
                    self.assertEqual((keys[0], keys[-1]), (0, 1))
                    self.assertEqual(keys, sorted(keys))


class CheckTest(Sandbox):
    def test_a_row_that_wraps_on_a_phone_is_caught(self):
        self.build()
        text = self.readme().replace('width="18.5%"', 'width="19%"')
        with open(bp.README, "w", encoding="utf8") as fh:
            fh.write(text)
        self.assertTrue(any("wraps on a phone" in err for err in bp.check()))

    def test_missing_images_alt_text_links_and_anchors_are_caught(self):
        self.build()
        with open(bp.README, "a", encoding="utf8") as fh:
            fh.write('\n<p><img src="./assets/nope.svg" width="10%"></p>\n<a href="nothing.pdf">x</a> <a href="#nowhere">y</a>\n')
        errors = "\n".join(bp.check())
        for expected in ("no alt text", "missing image ./assets/nope.svg", "broken link nothing.pdf", "no anchor named nowhere"):
            self.assertIn(expected, errors)


class CardTest(unittest.TestCase):
    @staticmethod
    def repo(stars, lic):
        return dict(name="swingbus", description="", primaryLanguage=None, latestRelease=None, stargazerCount=stars,
                    licenseInfo={"spdxId": lic} if lic else None)

    def test_a_card_shows_the_license_until_ten_stars(self):
        self.assertEqual(bp.facts(self.repo(1, "MIT"))["badge"], "MIT license")
        self.assertEqual(bp.facts(self.repo(12, "MIT"))["badge"], "12 stars")
        self.assertEqual(bp.facts(self.repo(1, None))["badge"], "")
        self.assertEqual(bp.facts(self.repo(1, "NOASSERTION"))["badge"], "")


class TimelineTest(unittest.TestCase):
    def test_key_times_are_padded_and_a_repeated_instant_keeps_the_later_value(self):
        self.assertEqual(bp.timeline([(0, 0), (0, 1), (.5, 0)]), ("0;0.5;1", "1;0;0"))
        self.assertEqual(bp.timeline([(.25, "a"), (.75, "b")]), ("0;0.25;0.75;1", "a;a;b;b"))


if __name__ == "__main__":
    unittest.main()
