#!/usr/bin/env python3
"""
Convert a UK AQ hex-map SVG back into a GeoJSON FeatureCollection.

Designed for the UK AQ LAD hex workflow:

    original LAD GeoJSON
      -> no-text SVG with one <path> per LA and GSS code IDs
      -> edit in Inkscape
      -> this script
      -> custom Wales/Scotland GeoJSON for the website

Examples:

    # Wales
    python3 svg_hex_to_geojson.py \
      --input-svg wales_hex_custom_2025.svg \
      --reference-geojson data/LAD/uk_aq_la_hex_2025.geojson \
      --region Wales \
      --output-geojson data/LAD/uk_aq_la_wales_hex_custom_2025.geojson

    # Scotland
    python3 svg_hex_to_geojson.py \
      --input-svg scotland_hex_custom_2025.svg \
      --reference-geojson data/LAD/uk_aq_la_hex_2025.geojson \
      --region Scotland \
      --output-geojson data/LAD/uk_aq_la_scotland_hex_custom_2025.geojson

What it does:
- Reads vector <path> geometry from the SVG.
- Uses path id or data-la-code as the LA code.
- Copies properties from the reference GeoJSON, so metadata is preserved.
- Writes one Feature per LA.
- Converts SVG Y-down coordinates back to GeoJSON-style Y-up coordinates.
- Applies simple SVG transforms: matrix(...), translate(...), scale(...).
- Supports path commands M, L, H, V, Z and their lowercase relative forms.
- Fails if the SVG contains raster <image> elements, unless --allow-images is set.

Important:
- The SVG must contain vector paths, not a PNG wrapped in SVG.
- Each LA path must have an id or data-la-code like W06000015 or S12000033.
- Do not use Inkscape Path > Union / Combine if that destroys the LA IDs.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


Point = Tuple[float, float]
Ring = List[Point]
Matrix = Tuple[float, float, float, float, float, float]  # a,b,c,d,e,f


COMMAND_RE = re.compile(r"[MmLlHhVvZz]|[-+]?(?:\d+\.\d+|\d+\.|\.\d+|\d+)(?:[eE][-+]?\d+)?")
TRANSFORM_RE = re.compile(r"([a-zA-Z]+)\s*\(([^)]*)\)")
NUMBER_RE = re.compile(r"[-+]?(?:\d+\.\d+|\d+\.|\.\d+|\d+)(?:[eE][-+]?\d+)?")
GSS_RE = re.compile(r"^[A-Z]\d{8}$")


def die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def strip_ns(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[1]
    return tag


def parse_floats(text: str) -> List[float]:
    return [float(x) for x in NUMBER_RE.findall(text)]


def mat_identity() -> Matrix:
    return (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


def mat_multiply(m1: Matrix, m2: Matrix) -> Matrix:
    # SVG affine matrices:
    # x' = a*x + c*y + e
    # y' = b*x + d*y + f
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (
        a1 * a2 + c1 * b2,
        b1 * a2 + d1 * b2,
        a1 * c2 + c1 * d2,
        b1 * c2 + d1 * d2,
        a1 * e2 + c1 * f2 + e1,
        b1 * e2 + d1 * f2 + f1,
    )


def mat_apply(m: Matrix, p: Point) -> Point:
    a, b, c, d, e, f = m
    x, y = p
    return (a * x + c * y + e, b * x + d * y + f)


def parse_transform(transform: Optional[str]) -> Matrix:
    if not transform:
        return mat_identity()

    result = mat_identity()

    for name, args_text in TRANSFORM_RE.findall(transform):
        args = parse_floats(args_text)
        name = name.lower()

        if name == "matrix":
            if len(args) != 6:
                die(f"Bad matrix transform: {transform}")
            local: Matrix = tuple(args)  # type: ignore[assignment]

        elif name == "translate":
            if len(args) == 1:
                tx, ty = args[0], 0.0
            elif len(args) >= 2:
                tx, ty = args[0], args[1]
            else:
                die(f"Bad translate transform: {transform}")
            local = (1.0, 0.0, 0.0, 1.0, tx, ty)

        elif name == "scale":
            if len(args) == 1:
                sx, sy = args[0], args[0]
            elif len(args) >= 2:
                sx, sy = args[0], args[1]
            else:
                die(f"Bad scale transform: {transform}")
            local = (sx, 0.0, 0.0, sy, 0.0, 0.0)

        elif name == "rotate":
            # Basic support for rotate(angle) and rotate(angle cx cy).
            # Useful in case a user rotates a cluster in Inkscape.
            if not args:
                die(f"Bad rotate transform: {transform}")
            angle = math.radians(args[0])
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)
            rot: Matrix = (cos_a, sin_a, -sin_a, cos_a, 0.0, 0.0)
            if len(args) >= 3:
                cx, cy = args[1], args[2]
                to_origin: Matrix = (1.0, 0.0, 0.0, 1.0, -cx, -cy)
                back: Matrix = (1.0, 0.0, 0.0, 1.0, cx, cy)
                local = mat_multiply(back, mat_multiply(rot, to_origin))
            else:
                local = rot

        else:
            die(
                f"Unsupported SVG transform '{name}'. "
                "Flatten transforms in Inkscape or extend this script."
            )

        # SVG transform lists are applied left-to-right.
        result = mat_multiply(result, local)

    return result


def parse_path_d(d: str) -> List[Ring]:
    """
    Parse a path containing M/L/H/V/Z commands into one or more rings.

    This intentionally does not approximate curves. If curves appear, the SVG
    is no longer clean hex polygon geometry for this workflow.
    """
    tokens = COMMAND_RE.findall(d.replace(",", " "))
    if not tokens:
        return []

    rings: List[Ring] = []
    current_ring: Ring = []
    current: Point = (0.0, 0.0)
    start: Optional[Point] = None
    cmd: Optional[str] = None
    i = 0

    def is_command(tok: str) -> bool:
        return bool(re.fullmatch(r"[MmLlHhVvZz]", tok))

    def read_number() -> float:
        nonlocal i
        if i >= len(tokens) or is_command(tokens[i]):
            die(f"Expected number in path near token {i}: {d[:120]}...")
        value = float(tokens[i])
        i += 1
        return value

    def close_ring() -> None:
        nonlocal current_ring, start, current
        if current_ring:
            if start is not None and current_ring[-1] != start:
                current_ring.append(start)
            if len(current_ring) >= 4:
                rings.append(current_ring)
        current_ring = []
        start = None

    while i < len(tokens):
        tok = tokens[i]
        if is_command(tok):
            cmd = tok
            i += 1
            if cmd in "Zz":
                close_ring()
                continue
        elif cmd is None:
            die(f"Path does not start with a command: {d[:120]}...")

        if cmd in "Mm":
            # First pair is move. Additional pairs are implicit line commands.
            first = True
            while i < len(tokens) and not is_command(tokens[i]):
                x = read_number()
                y = read_number()
                if cmd == "m":
                    point = (current[0] + x, current[1] + y)
                else:
                    point = (x, y)
                current = point
                if first:
                    if current_ring:
                        close_ring()
                    current_ring = [point]
                    start = point
                    first = False
                else:
                    current_ring.append(point)
            cmd = "l" if cmd == "m" else "L"

        elif cmd in "Ll":
            while i < len(tokens) and not is_command(tokens[i]):
                x = read_number()
                y = read_number()
                point = (current[0] + x, current[1] + y) if cmd == "l" else (x, y)
                current = point
                current_ring.append(point)

        elif cmd in "Hh":
            while i < len(tokens) and not is_command(tokens[i]):
                x = read_number()
                point = (current[0] + x, current[1]) if cmd == "h" else (x, current[1])
                current = point
                current_ring.append(point)

        elif cmd in "Vv":
            while i < len(tokens) and not is_command(tokens[i]):
                y = read_number()
                point = (current[0], current[1] + y) if cmd == "v" else (current[0], y)
                current = point
                current_ring.append(point)

        else:
            die(
                f"Unsupported path command '{cmd}'. "
                "The SVG should contain polygonal M/L/H/V/Z paths only."
            )

    if current_ring:
        close_ring()

    return rings


def signed_area(ring: Ring) -> float:
    area = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:]):
        area += x1 * y2 - x2 * y1
    return area / 2.0


def ensure_closed(ring: Ring) -> Ring:
    if ring and ring[0] != ring[-1]:
        return ring + [ring[0]]
    return ring


def collect_paths(
    element: ET.Element,
    parent_matrix: Matrix,
    allow_images: bool,
) -> List[Tuple[Dict[str, str], str, Matrix]]:
    items: List[Tuple[Dict[str, str], str, Matrix]] = []
    local_matrix = mat_multiply(parent_matrix, parse_transform(element.attrib.get("transform")))
    tag = strip_ns(element.tag)

    if tag == "image" and not allow_images:
        die(
            "The SVG contains a raster <image> element. "
            "Open the vector SVG in Inkscape and use File > Save As > Plain SVG, not Export PNG."
        )

    if tag == "path":
        d = element.attrib.get("d")
        if d:
            items.append((dict(element.attrib), d, local_matrix))

    for child in list(element):
        items.extend(collect_paths(child, local_matrix, allow_images))

    return items


def get_la_code(attrs: Dict[str, str]) -> Optional[str]:
    candidates = [
        attrs.get("data-la-code"),
        attrs.get("data-la_code"),
        attrs.get("la_code"),
        attrs.get("id"),
    ]
    for candidate in candidates:
        if candidate and GSS_RE.match(candidate):
            return candidate
    return None


def bbox_of_rings(rings_by_code: Dict[str, List[Ring]]) -> Tuple[float, float, float, float]:
    xs: List[float] = []
    ys: List[float] = []
    for rings in rings_by_code.values():
        for ring in rings:
            for x, y in ring:
                xs.append(x)
                ys.append(y)
    if not xs or not ys:
        die("No coordinates found for bounding box")
    return min(xs), min(ys), max(xs), max(ys)


def bbox_of_features(features: Sequence[Dict[str, Any]]) -> Tuple[float, float, float, float]:
    xs: List[float] = []
    ys: List[float] = []

    def walk_coords(obj: Any) -> None:
        if (
            isinstance(obj, list)
            and len(obj) >= 2
            and isinstance(obj[0], (int, float))
            and isinstance(obj[1], (int, float))
        ):
            xs.append(float(obj[0]))
            ys.append(float(obj[1]))
        elif isinstance(obj, list):
            for item in obj:
                walk_coords(item)

    for feature in features:
        geom = feature.get("geometry") or {}
        walk_coords(geom.get("coordinates"))

    if not xs or not ys:
        die("No reference GeoJSON coordinates found for bounding box")
    return min(xs), min(ys), max(xs), max(ys)


def transform_svg_to_reference(
    rings_by_code: Dict[str, List[Ring]],
    ref_features: Sequence[Dict[str, Any]],
) -> Dict[str, List[Ring]]:
    """
    Fit edited SVG coordinates into the coordinate extent of the reference region.

    SVG uses Y-down; the reference cartogram coordinates use Y-up. This maps
    the edited SVG path bounding box to the reference region bounding box using
    a uniform scale (same factor for X and Y) so that hexagon proportions are
    preserved. The SVG and the reference region may have different aspect ratios
    (e.g. landscape SVG vs portrait reference), so using separate X and Y scales
    would squish the hexagons.
    """
    svg_minx, svg_miny, svg_maxx, svg_maxy = bbox_of_rings(rings_by_code)
    ref_minx, ref_miny, ref_maxx, ref_maxy = bbox_of_features(ref_features)

    svg_w = svg_maxx - svg_minx
    svg_h = svg_maxy - svg_miny
    ref_w = ref_maxx - ref_minx
    ref_h = ref_maxy - ref_miny

    if svg_w <= 0 or svg_h <= 0 or ref_w <= 0 or ref_h <= 0:
        die("Invalid zero-width/height bounding box during coordinate conversion")

    # Uniform scale: pick the factor that fits the tighter dimension.
    # This keeps hex shapes undistorted regardless of SVG vs reference aspect ratio.
    s = min(ref_w / svg_w, ref_h / svg_h)

    converted: Dict[str, List[Ring]] = {}
    for code, rings in rings_by_code.items():
        out_rings: List[Ring] = []
        for ring in rings:
            new_ring: Ring = []
            for x, y in ring:
                gx = ref_minx + (x - svg_minx) * s
                gy = ref_maxy - (y - svg_miny) * s  # Y flip: SVG Y-down → GeoJSON Y-up
                new_ring.append((gx, gy))
            out_rings.append(ensure_closed(new_ring))
        converted[code] = out_rings

    return converted


def rings_to_geometry(rings: List[Ring]) -> Dict[str, Any]:
    """
    Output MultiPolygon geometry. Each SVG subpath becomes one polygon.
    This is simple and robust for the UK AQ hex shapes, where paths normally
    represent joined hex outlines.
    """
    polygons = []
    for ring in rings:
        ring = ensure_closed(ring)
        if len(ring) < 4:
            continue

        # GeoJSON recommends exterior rings use right-hand rule, but most web
        # renderers do not require it. We keep a consistent orientation.
        if signed_area(ring) < 0:
            ring = list(reversed(ring))

        polygons.append([[[round(x, 9), round(y, 9)] for x, y in ring]])

    if not polygons:
        die("A feature produced no valid polygon rings")

    return {
        "type": "MultiPolygon",
        "coordinates": polygons,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert UK AQ LA SVG paths to GeoJSON")
    parser.add_argument("--input-svg", required=True, help="Input cleaned vector SVG")
    parser.add_argument("--output-geojson", required=True, help="Output GeoJSON path")
    parser.add_argument(
        "--reference-geojson",
        required=True,
        help="Canonical full LAD GeoJSON used to copy properties and region bbox",
    )
    parser.add_argument(
        "--region",
        required=True,
        help='Region/nation to extract from reference, e.g. "Wales" or "Scotland"',
    )
    parser.add_argument(
        "--allow-images",
        action="store_true",
        help="Do not fail on SVG <image> elements. Not recommended.",
    )
    parser.add_argument(
        "--keep-svg-coordinates",
        action="store_true",
        help=(
            "Write SVG coordinates directly instead of fitting them into the "
            "reference GeoJSON region bbox. Usually leave this off."
        ),
    )
    args = parser.parse_args()

    svg_path = Path(args.input_svg)
    out_path = Path(args.output_geojson)
    ref_path = Path(args.reference_geojson)

    if not svg_path.exists():
        die(f"Input SVG not found: {svg_path}")
    if not ref_path.exists():
        die(f"Reference GeoJSON not found: {ref_path}")

    try:
        root = ET.parse(svg_path).getroot()
    except ET.ParseError as exc:
        die(f"Could not parse SVG XML: {exc}")

    try:
        reference = json.loads(ref_path.read_text(encoding="utf-8"))
    except Exception as exc:
        die(f"Could not read reference GeoJSON: {exc}")

    if reference.get("type") != "FeatureCollection":
        die("Reference file is not a GeoJSON FeatureCollection")

    ref_features = [
        f
        for f in reference.get("features", [])
        if (f.get("properties") or {}).get("region_nation") == args.region
    ]

    if not ref_features:
        die(f"No reference features found for region_nation == {args.region!r}")

    ref_by_code: Dict[str, Dict[str, Any]] = {}
    for feature in ref_features:
        props = feature.get("properties") or {}
        code = props.get("la_code")
        if not code:
            die("Reference feature missing properties.la_code")
        if code in ref_by_code:
            die(f"Duplicate reference la_code: {code}")
        ref_by_code[code] = feature

    svg_paths = collect_paths(root, mat_identity(), args.allow_images)

    rings_by_code: Dict[str, List[Ring]] = {}
    ignored_paths = 0

    for attrs, d, matrix in svg_paths:
        code = get_la_code(attrs)
        if not code:
            ignored_paths += 1
            continue

        rings = parse_path_d(d)
        transformed_rings: List[Ring] = []
        for ring in rings:
            transformed = [mat_apply(matrix, p) for p in ring]
            transformed_rings.append(ensure_closed(transformed))

        if not transformed_rings:
            die(f"No usable rings found for SVG path {code}")

        if code in rings_by_code:
            # Multiple paths for the same LA are allowed; merge as separate polygons.
            rings_by_code[code].extend(transformed_rings)
        else:
            rings_by_code[code] = transformed_rings

    if not rings_by_code:
        die("No SVG paths with LA codes were found")

    expected_codes = set(ref_by_code)
    found_codes = set(rings_by_code)

    missing = sorted(expected_codes - found_codes)
    extra = sorted(found_codes - expected_codes)

    if missing:
        die(f"SVG is missing {len(missing)} expected {args.region} LA codes: {', '.join(missing)}")
    if extra:
        die(f"SVG contains {len(extra)} LA codes not in reference {args.region}: {', '.join(extra)}")

    if args.keep_svg_coordinates:
        converted = rings_by_code
    else:
        converted = transform_svg_to_reference(rings_by_code, ref_features)

    output_features: List[Dict[str, Any]] = []
    for feature in ref_features:
        props = dict(feature.get("properties") or {})
        code = props["la_code"]
        geom = rings_to_geometry(converted[code])
        output_features.append(
            {
                "type": "Feature",
                "properties": props,
                "geometry": geom,
            }
        )

    output = {
        "type": "FeatureCollection",
        "name": f"uk_aq_la_{args.region.lower().replace(' ', '_')}_hex_custom_2025",
        "features": output_features,
    }

    # Add bbox
    minx, miny, maxx, maxy = bbox_of_features(output_features)
    output["bbox"] = [round(minx, 9), round(miny, 9), round(maxx, 9), round(maxy, 9)]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

    print("Converted SVG to GeoJSON")
    print(f"  SVG: {svg_path}")
    print(f"  Reference GeoJSON: {ref_path}")
    print(f"  Region: {args.region}")
    print(f"  SVG paths with LA codes: {len(rings_by_code)}")
    print(f"  Ignored paths without LA code: {ignored_paths}")
    print(f"  Features written: {len(output_features)}")
    print(f"  Output: {out_path}")
    print("  Validation: OK")


if __name__ == "__main__":
    main()
