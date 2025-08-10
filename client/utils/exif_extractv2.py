"""
Robust EXIF -> camera context pipeline for Throughline.

Features:
- safe EXIF extraction (piexif) with exceptions handled
- robust rational and GPS parsing (rat2float accepts many forms)
- exact shutter pretty formatting using Fraction.limit_denominator
- safe GPS hemisphere sign application
- defensive timestamp parsing (DateTimeOriginal + OffsetTimeOriginal)
- simple golden-hour / day / night heuristic (no astral dependency)
- produces both machine-friendly fields and human-friendly pretty strings
- camera_context_block formats a compact bullet list for LLM prompts
"""

from __future__ import annotations
import piexif
from datetime import datetime
from fractions import Fraction
from typing import Any, Dict, Optional
import logging
import unittest
from typing import Optional
from typing import cast


log = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARNING)

# Useful tags we look for
USEFUL_TAGS = {
    "FNumber",
    "ExposureTime",
    "ISOSpeedRatings",
    "WhiteBalance",
    "DateTimeOriginal",
    "OffsetTimeOriginal",
    "GPSLatitude",
    "GPSLongitude",
    "GPSLatitudeRef",
    "GPSLongitudeRef",
    # vendor color temp names (optional)
    "ColorTemperature", "ColorTemp", "Temperature",
}

# -------------------------
# Extraction
# -------------------------
def extract_exif_raw(image_path: str) -> Dict[str, Any]:
    """Return flat dict tag_name -> raw value. Return {} on errors or no EXIF."""
    try:
        # build tag lookup (if piexif has changed this will still be guarded)
        ALL_TAGS = {
            (ifd, tag_id): info["name"]
            for ifd, tag_dict in piexif.TAGS.items()
            for tag_id, info in tag_dict.items()
        }
    except Exception:
        ALL_TAGS = {}

    try:
        raw = piexif.load(image_path)
    except Exception as e:
        log.debug("piexif.load failed for %s: %s", image_path, e)
        return {}

    flat: Dict[str, Any] = {}
    for ifd_name, ifd in raw.items():
        if ifd_name == "thumbnail" or ifd is None:
            continue
        if isinstance(ifd, dict):
            for tag_id, val in ifd.items():
                name = ALL_TAGS.get((ifd_name, tag_id), f"{ifd_name}:{tag_id}")
                flat[name] = val
    return flat

def filter_exif(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only tags relevant to our analysis."""
    return {k: raw[k] for k in USEFUL_TAGS if k in raw}

# -------------------------
# Normalization helpers
# -------------------------
def _safe_decode(b: Any) -> Any:
    if isinstance(b, bytes):
        try:
            return b.decode(errors="ignore")
        except Exception:
            return b
    return b

def rat2float(r: Any) -> Optional[float]:
    """
    Convert EXIF numeric forms to float:
    - (num, den) => num/den
    - ((dnum, dden),(mnum,mden),(snum,sden)) => decimal degrees
    - single-element tuple/list => take first element
    - int/float/str numeric => float
    - else => None
    """
    if r is None:
        return None

    # single-element tuple/list -> treat as scalar
    if isinstance(r, (list, tuple)) and len(r) == 1:
        return rat2float(r[0])

    # GPS triple: ((deg_num,deg_den),(min_num,min_den),(sec_num,sec_den))
    if (
        isinstance(r, (list, tuple))
        and len(r) == 3
        and all(isinstance(comp, (list, tuple)) and len(comp) == 2 for comp in r)
    ):
        try:
            deg = float(r[0][0]) / float(r[0][1]) if r[0][1] != 0 else None
            mins = float(r[1][0]) / float(r[1][1]) if r[1][1] != 0 else None
            secs = float(r[2][0]) / float(r[2][1]) if r[2][1] != 0 else None
            if deg is None or mins is None or secs is None:
                return None
            return deg + mins / 60.0 + secs / 3600.0
        except Exception:
            return None

    # Simple rational (num, den)
    if isinstance(r, (list, tuple)) and len(r) == 2:
        num, den = r
        try:
            den_f = float(den)
            if den_f == 0:
                return None
            return float(num) / den_f
        except Exception:
            return None

    # ints/floats
    if isinstance(r, (int, float)):
        try:
            return float(r)
        except Exception:
            return None

    # numeric strings/bytes
    if isinstance(r, (bytes, str)):
        s = _safe_decode(r)
        try:
            return float(s)
        except Exception:
            # try to strip common non-numeric chars
            try:
                s2 = str(s).strip()
                return float(s2)
            except Exception:
                return None

    return None

def format_shutter(shutter_s: Optional[float]) -> Optional[str]:
    """
    Create pretty shutter string:
    - For <1s use rational string like '1/125s' or '2/3s' if fraction not unitary
    - For >=1s use '2.0s'
    - Return None for invalid/zero/negative inputs
    """
    if shutter_s is None:
        return None
    try:
        ss = float(shutter_s)
    except Exception:
        return None
    if ss <= 0:
        return None

    # For reciprocal style: prefer exact fraction with reasonable denominator cap
    if ss < 1.0:
        frac = Fraction(ss).limit_denominator(8000)  # common max shutter denominator
        # Represent as '1/125s' or '2/3s' as needed
        if frac.numerator == 1:
            return f"1/{frac.denominator}s"
        else:
            return f"{frac.numerator}/{frac.denominator}s"
    else:
        # seconds with 1 decimal place for readability
        return f"{round(ss, 1)}s"

def pretty_aperture(ap: Optional[float]) -> Optional[str]:
    if ap is None:
        return None
    try:
        return f"f/{round(float(ap), 1)}"
    except Exception:
        return None

# -------------------------
# Normalize exif
# -------------------------
PROG_MAP = {
    1: "Manual", 2: "Program AE", 3: "Aperture-Priority", 4: "Shutter-Priority",
    5: "Creative Program", 6: "Action Program"
}
METERING_MAP = {
    0: "Unknown", 1: "Average", 2: "Center-weighted", 3: "Spot",
    4: "Multi-spot", 5: "Pattern"
}

def normalize_exif(filt: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a normalized context dict. Use safe conversions; missing keys produce None.
    Keys include:
      - iso (float)
      - aperture (float) and aperture_pretty (str)
      - shutter_s (float) and shutter_pretty (str)
      - ev_bias, brightness_ev, shutter_ev, aperture_ev (floats or None)
      - prog (human string) and metering
      - white_balance (Auto/Manual/None) and white_balance_kelvin (int or None)
      - focal_35mm, zoom
      - timestamp_raw (str) for interpret_context parsing
      - gps: dict with lat, lon, lat_ref, lon_ref (lat/lon numeric or None)
    """
    ctx: Dict[str, Any] = {}

    # ISO (may be int, tuple, list)
    iso_raw = filt.get("ISOSpeedRatings")
    try:
        if isinstance(iso_raw, (list, tuple)) and len(iso_raw) >= 1:
            iso_val = iso_raw[0]
        else:
            iso_val = iso_raw
        ctx["iso"] = rat2float(iso_val)
    except Exception:
        ctx["iso"] = None

    # Aperture
    ctx["aperture"] = rat2float(filt.get("FNumber"))
    ctx["aperture_pretty"] = pretty_aperture(ctx["aperture"])

    # Shutter
    ctx["shutter_s"] = rat2float(filt.get("ExposureTime"))
    ctx["shutter_pretty"] = format_shutter(ctx["shutter_s"])

    # EVs
    ctx["ev_bias"] = rat2float(filt.get("ExposureBiasValue"))
    ctx["brightness_ev"] = rat2float(filt.get("BrightnessValue"))
    ctx["shutter_ev"] = rat2float(filt.get("ShutterSpeedValue"))
    ctx["aperture_ev"] = rat2float(filt.get("ApertureValue"))

    # Program & metering (may be absent)
    prog_val = filt.get("ExposureProgram")
    ctx["prog"] = PROG_MAP.get(prog_val) if prog_val is not None else None
    meter_val = filt.get("MeteringMode")
    ctx["metering"] = METERING_MAP.get(meter_val) if meter_val is not None else None

    # White balance
    wb = filt.get("WhiteBalance")
    if wb is not None:
        # many cameras use 0=Auto, 1=Manual
        try:
            wb_int = int(wb)
            ctx["white_balance"] = "Auto" if wb_int == 0 else "Manual"
        except Exception:
            ctx["white_balance"] = str(wb)
    else:
        ctx["white_balance"] = None

    # Kelvin temp if present (various tag names)
    ctx["white_balance_kelvin"] = None
    for name in ("ColorTemperature", "ColorTemp", "Temperature"):
        if name in filt:
            k = rat2float(filt.get(name))
            if k is not None:
                try:
                    ctx["white_balance_kelvin"] = int(round(k))
                except Exception:
                    ctx["white_balance_kelvin"] = None
            break

    # focal length 35mm & zoom
    ctx["focal_35mm"] = rat2float(filt.get("FocalLengthIn35mmFilm"))
    ctx["zoom"] = rat2float(filt.get("DigitalZoomRatio")) or 1.0

    # Timestamp raw (keep string for interpret_context)
    dto = filt.get("DateTimeOriginal")
    off = filt.get("OffsetTimeOriginal") or filt.get("OffsetTime")
    if dto is not None:
        dto_s = _safe_decode(dto)
        off_s = _safe_decode(off) if off is not None else ""
        # combine but keep safe; interpret_context will parse more robustly
        ctx["timestamp_raw"] = (str(dto_s) + str(off_s)).strip()
    else:
        ctx["timestamp_raw"] = None

    # GPS
    lat = rat2float(filt.get("GPSLatitude"))
    lon = rat2float(filt.get("GPSLongitude"))
    latref = _safe_decode(filt.get("GPSLatitudeRef")) if filt.get("GPSLatitudeRef") else None
    lonref = _safe_decode(filt.get("GPSLongitudeRef")) if filt.get("GPSLongitudeRef") else None

    # Apply hemisphere signs only if numeric lat/lon present
    if lat is not None and isinstance(lat, (int, float)):
        if latref and str(latref).upper().startswith("S"):
            lat = -abs(lat)
    if lon is not None and isinstance(lon, (int, float)):
        if lonref and str(lonref).upper().startswith("W"):
            lon = -abs(lon)

    ctx["gps"] = {"lat": lat, "lon": lon, "lat_ref": latref, "lon_ref": lonref}

    return ctx

# -------------------------
# Interpretation (no astral)
# -------------------------
def interpret_context(ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add derived flags: motion_risk, dof_hint, time_of_day using fallback heuristics.
    time_of_day heuristic:
      - 05:00-07:00 => golden_hour_morning
      - 17:00-19:00 => golden_hour_evening
      - 07:00-17:00 => daytime
      - otherwise => night
    """
    out = dict(ctx)  # copy to avoid mutating caller

    # Motion risk (handheld blur risk): thresholds conservative
    try:
        s = out.get("shutter_s")
        if s is None:
            out["motion_risk"] = "unknown"
        else:
            s_f = float(s)
            out["motion_risk"] = "high" if s_f > 0.04 else "low"
    except Exception:
        out["motion_risk"] = "unknown"

    # DOF hint
    try:
        a = out.get("aperture")
        if a is None:
            out["dof_hint"] = "unknown"
        else:
            a_f = float(a)
            if a_f <= 2.8:
                out["dof_hint"] = "shallow"
            elif a_f >= 8.0:
                out["dof_hint"] = "deep"
            else:
                out["dof_hint"] = "moderate"
    except Exception:
        out["dof_hint"] = "unknown"

    # Time of day (fallback heuristic; accurate enough for LLM context without astral)
    tod = "unknown"
    ts_raw = out.get("timestamp_raw")
    if ts_raw:
        # Try to normalize timestamp formats
        try:
            s = str(ts_raw).strip()
            # EXIF typical: "YYYY:MM:DD HH:MM:SS" optionally with '+HH:MM'
            # convert leading date colons to dashes for fromisoformat compatibility
            if len(s) >= 19 and s[4] == ":" and s[7] == ":":
                s_mod = s.replace(":", "-", 2)  # change only first two colons -> 'YYYY-MM-DD HH:MM:SS...'
            else:
                s_mod = s
            # replace space with T to try ISO parser if offset present
            s_iso = s_mod.replace(" ", "T", 1)
            # try fromisoformat (handles offsets if present)
            try:
                dt = datetime.fromisoformat(s_iso)
            except Exception:
                # fallback to strict parse without offset
                dt = datetime.strptime(s_mod[:19], "%Y-%m-%d %H:%M:%S")
            hour = dt.hour
            if 5 <= hour < 7:
                tod = "golden_hour_morning"
            elif 17 <= hour < 19:
                tod = "golden_hour_evening"
            elif 7 <= hour < 17:
                tod = "daytime"
            else:
                tod = "night"
        except Exception:
            tod = "unknown"
    out["time_of_day"] = tod

    return out

# -------------------------
# Pipeline & formatting
# -------------------------
def build_camera_context(image_path: str) -> Dict[str, Any]:
    raw = extract_exif_raw(image_path)
    if not raw:
        # return an empty but consistent structure to avoid crashes downstream
        return {
            "iso": None,
            "aperture": None,
            "aperture_pretty": None,
            "shutter_s": None,
            "shutter_pretty": None,
            "ev_bias": None,
            "brightness_ev": None,
            "shutter_ev": None,
            "aperture_ev": None,
            "prog": None,
            "metering": None,
            "white_balance": None,
            "white_balance_kelvin": None,
            "focal_35mm": None,
            "zoom": None,
            "timestamp_raw": None,
            "gps": {"lat": None, "lon": None, "lat_ref": None, "lon_ref": None},
            "motion_risk": "unknown",
            "dof_hint": "unknown",
            "time_of_day": "unknown",
        }

    filt = filter_exif(raw)
    norm = normalize_exif(filt)
    full = interpret_context(norm)
    return full

def camera_context_block(ctx: Dict[str, Any]) -> str:
    """Format ctx dict into a compact bullet list for LLM prompts. Filters empty/None values."""
    lines = []
    for k, v in ctx.items():
        # skip empty/None
        if v is None:
            continue
        if isinstance(v, dict):
            # only include inner values that are not None
            inner = ", ".join(f"{ik}: {iv}" for ik, iv in v.items() if iv is not None)
            if inner:
                lines.append(f"- {k.replace('_',' ').title()}: {inner}")
        else:
            lines.append(f"- {k.replace('_',' ').title()}: {v}")
    return "\n".join(lines)

# -------------------------
# Unit tests (basic)
# -------------------------
class TestCameraContextBasic(unittest.TestCase):

    def test_rat2float_simple(self):
        self.assertEqual(rat2float((1, 2)), 0.5)

    def test_rat2float_zero_den(self):
        self.assertIsNone(rat2float((5, 0)))

    def test_rat2float_gps(self):
        val = rat2float(((12, 1), (30, 1), (0, 1)))
        self.assertIsNotNone(val)
        val = cast(float, val) #typeerror ho rha tha bahut, abhi ke liye kaam chalau yeh
        self.assertAlmostEqual(val, 12.5, places=6) #naye unittest stub se kaam chala rha 
        
    # def test_rat2float_gps(self):
    #     val: Optional[float] = rat2float(((12, 1), (30, 1), (0, 1)))
    #     self.assertIsNotNone(val)
    #     # At this point val is known not to be None
    #     #self.assertAlmostEqual(val, 12.5, 6) #temp fix by making unittest.pyi and usme syntax dediya
    #     #self.assertAlmostEqual(val, 12.5, delta=1e-6)
    #     self.assertAlmostEqual(self, val, 12.5, places=6)

        '''val: float = rat2float(((12, 1), (30, 1), (0, 1)))
        self.assertIsNotNone(val)
        self.assertAlmostEqual(val, 12.5, places=6)'''
        '''val = rat2float(((12, 1), (30, 1), (0, 1)))
        self.assertIsNotNone(val)
        self.assertAlmostEqual(val, 12.5, places=6)'''
        

    def test_format_shutter(self):
        self.assertEqual(format_shutter(0.008), "1/125s")
        self.assertEqual(format_shutter(2.0), "2.0s")
        self.assertIsNone(format_shutter(0))
        self.assertIsNone(format_shutter(None))

    def test_normalize_and_interpret(self):
        filt = {
            "FNumber": (28, 10),
            "ExposureTime": (1, 125),
            "ISOSpeedRatings": (100,),
            "DateTimeOriginal": b"2023:01:01 06:00:00",
            "GPSLatitude": ((12,1),(30,1),(0,1)),
            "GPSLatitudeRef": b"N",
            "GPSLongitude": ((77,1),(36,1),(0,1)),
            "GPSLongitudeRef": b"E",
        }
        norm = normalize_exif(filt)
        self.assertAlmostEqual(norm["aperture"], 2.8, places=3)
        self.assertEqual(norm["aperture_pretty"], "f/2.8")
        self.assertEqual(norm["shutter_pretty"], "1/125s")
        full = interpret_context(norm)
        self.assertIn(full["time_of_day"], ("golden_hour_morning", "golden_hour_evening", "daytime", "night"))

if __name__ == "__main__":
    # run tests when invoked as script, or show a demo if a path argument is provided
    import sys
    if len(sys.argv) == 1:
        unittest.main(argv=[sys.argv[0]])
    else:
        p = sys.argv[1]
        ctx = build_camera_context(p)
        print("Camera Context:\n", camera_context_block(ctx))
