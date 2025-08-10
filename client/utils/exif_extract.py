"""
utils/camera_context.py
exif data extractions
this module reads an image's EXIF metadata, pulls out technical camera data (aperture, shutter speed, ISO, etc.), 
interprets it into simple categories (motion risk, time of day), and formats it for an LLM to consume.
"""

import piexif
import datetime
import unittest

# ─── EXIF EXTRACTION ─────────────────────────────────────────────

def extract_exif_raw(image_path: str) -> dict:
    """Load all EXIF tags into a flat dict of tag-name → raw value."""
    # Build (ifd_name, tag_id) → tag_name lookup
    ALL_TAGS = {
        (ifd, tag_id): info["name"]
        for ifd, tag_dict in piexif.TAGS.items()
        for tag_id, info in tag_dict.items()
    }

    raw = piexif.load(image_path)
    exif = {}
    for ifd_name, ifd in raw.items():
        if ifd_name == "thumbnail":
            continue
        for tag_id, val in ifd.items():
            name = ALL_TAGS.get((ifd_name, tag_id), f"Unknown_{tag_id}")
            exif[name] = val
    return exif

USEFUL_TAGS = {
    "ExposureTime","FNumber","ISOSpeedRatings","ExposureBiasValue",
    "BrightnessValue","ShutterSpeedValue","ApertureValue","ExposureProgram",
    "MeteringMode","WhiteBalance","FocalLengthIn35mmFilm",
    "DigitalZoomRatio","DateTimeOriginal","OffsetTimeOriginal",
    "GPSLatitude","GPSLongitude"
}

def filter_exif(raw: dict) -> dict:
    """Keep only the tags we actually use for feedback."""
    return {k: raw[k] for k in USEFUL_TAGS if k in raw}

# ─── NORMALIZATION ───────────────────────────────────────────────

def rat2float(r):
    """
    Convert:
     - simple (num, den) EXIF rationals → float
     - GPS tuples → decimal degrees
     - simple scalars (int, float, numeric strings) → float
     - everything else → None
    """
    # Simple rational
    if isinstance(r, tuple) and len(r) == 2:
        num, den = r
        try:
            return num / den
        except (TypeError, ZeroDivisionError):
            return None

    # GPS-style tuple
    if (
        isinstance(r, tuple) and len(r) == 3
        and all(isinstance(x, tuple) and len(x) == 2 for x in r)
    ):
        try:
            deg = r[0][0] / r[0][1]
            mins = r[1][0] / r[1][1]
            secs = r[2][0] / r[2][1]
            return deg + mins / 60 + secs / 3600
        except (TypeError, ZeroDivisionError, IndexError):
            return None

    # Fallback: only convert simple scalars
    if isinstance(r, (int, float, str)):
        try:
            return float(r)
        except (TypeError, ValueError):
            return None

    # Anything else (e.g. arbitrary tuple) → None
    return None

METERING_MAP = {
    1: "Average", 2: "Center-weighted", 3: "Spot",
    4: "Multi-spot", 5: "Pattern"
}
PROG_MAP = {
    1: "Manual", 2: "Program AE",
    3: "Aperture-Priority", 4: "Shutter-Priority"
}

def normalize_exif(filt: dict) -> dict:
    """Convert raw EXIF values into typed, human-friendly context."""
    ctx = {}
    ctx["iso"]            = filt.get("ISOSpeedRatings")
    ctx["aperture"]       = rat2float(filt.get("FNumber"))
    ctx["shutter_s"]      = rat2float(filt.get("ExposureTime"))
    ctx["ev_bias"]        = rat2float(filt.get("ExposureBiasValue"))
    ctx["brightness_ev"]  = rat2float(filt.get("BrightnessValue"))
    ctx["shutter_ev"]     = rat2float(filt.get("ShutterSpeedValue"))
    ctx["aperture_ev"]    = rat2float(filt.get("ApertureValue"))
    prog_val = filt.get("ExposureProgram")
    ctx["prog"] = PROG_MAP[prog_val] if prog_val in PROG_MAP else "Unknown"

    
    meter_val = filt.get("MeteringMode")
    ctx["metering"] = METERING_MAP[meter_val] if meter_val in METERING_MAP else "Unknown"

    #ctx["prog"]           = PROG_MAP.get(filt.get("ExposureProgram"), "Unknown")
    #ctx["metering"]       = METERING_MAP.get(filt.get("MeteringMode"), "Unknown")
    wb = filt.get("WhiteBalance")
    ctx["white_balance"]  = "Auto" if wb == 0 else "Manual"
    ctx["focal_35mm"]     = filt.get("FocalLengthIn35mmFilm")
    ctx["zoom"]           = rat2float(filt.get("DigitalZoomRatio")) or 1.0

    # timestamp
    dto = filt.get("DateTimeOriginal")
    off = filt.get("OffsetTimeOriginal", "")
    if dto:
        t = dto.decode() if isinstance(dto, bytes) else dto
        z = off.decode() if isinstance(off, bytes) else off
        ctx["timestamp"] = t + z

    # GPS
    lat = rat2float(filt.get("GPSLatitude"))
    lon = rat2float(filt.get("GPSLongitude"))
    ctx["gps"] = {"lat": lat, "lon": lon}

    return ctx

# ─── INTERPRETATION ─────────────────────────────────────────────

def interpret_context(ctx: dict) -> dict:
    """Derive simple flags: motion risk, DOF hint, time-of-day bucket."""
    s = ctx.get("shutter_s")
    if s is not None:
        ctx["motion_risk"] = "high" if s > 0.04 else "low"
    a = ctx.get("aperture")
    ctx["dof_hint"] = "shallow" if a is not None and a <= 2.8 else "deep"

    ts = ctx.get("timestamp")
    if ts:
        try:
            dt = datetime.datetime.fromisoformat(ts.replace(" ", "T"))
            h = dt.hour
            if 5 < h < 7 or 17 < h < 19:
                ctx["time_of_day"] = "golden_hour" #hardcoded logic -> aage work karega weather api se; right now not factually true.
            elif 7 <= h < 17:
                ctx["time_of_day"] = "daytime" 
            else:
                ctx["time_of_day"] = "night"
        except:
            ctx["time_of_day"] = "unknown"

    return ctx

# ─── PIPELINE & FORMATTING ───────────────────────────────────────

def build_camera_context(image_path: str) -> dict:
    raw  = extract_exif_raw(image_path)
    filt = filter_exif(raw)
    norm = normalize_exif(filt)
    full = interpret_context(norm)
    return full

def camera_context_block(ctx: dict) -> str:
    """Format the context dict as a bullet list for LLM prompts."""
    lines = []
    for k, v in ctx.items():
        if v is None or v == "" or (isinstance(v, dict) and not any(v.values())):
            continue
        lines.append(f"- {k.replace('_',' ').title()}: {v}")
    return "\n".join(lines)

# ─── UNIT TESTS ─────────────────────────────────────────────────

class TestCameraContext(unittest.TestCase):
    def test_rat2float(self):
        self.assertEqual(rat2float((1,2)), 0.5)
        self.assertEqual(rat2float((0,5)), 0.0)
        self.assertIsNone(rat2float((5,0)))
        #self.assertAlmostEqual(rat2float(((12,1),(30,1),(0,1))), 12.5)
        val = rat2float(((12,1),(30,1),(0,1)))
        assert isinstance(val, float)  # this satisfies both Pylance and safety
        self.assertAlmostEqual(val, 12.5)

    def test_normalize_missing(self):
        ctx = normalize_exif({})
        self.assertIn("iso", ctx)
        self.assertIsNone(ctx["iso"])

    def test_timestamp(self):
        exif = {"DateTimeOriginal": b"2023:01:01 15:00:00", "OffsetTimeOriginal": b"+00:00"}
        ctx = normalize_exif(exif)
        full = interpret_context(ctx)
        self.assertIn("time_of_day", full)

if __name__ == "__main__":
    import sys
    if len(sys.argv) == 1:
        # run tests
        unittest.main(argv=[sys.argv[0]])
    else:
        # demo on provided image path
        path = sys.argv[1]
        ctx = build_camera_context(path)
        print("Camera Context:\n", camera_context_block(ctx))
