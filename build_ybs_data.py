#!/usr/bin/env python3
"""Build a validated, deduplicated Yangon YBS master JSON file.

The newer YBS-Data archive supplies bilingual stops and ordered route stop IDs.
The older ybs-data-json archive supplies comparison/legacy metadata. Its route
ID arrays are sorted membership sets, not travel order, so they are never used
as stop_sequence values.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import sys
import unicodedata
import zipfile
from collections import defaultdict
from pathlib import Path
from typing import Any


DEFAULT_NEWER_ARCHIVE = Path(r"C:\Users\Dell\Downloads\YBS-Data-master.zip")
DEFAULT_LEGACY_ARCHIVE = Path(r"C:\Users\Dell\Downloads\ybs-data-json-master.zip")


# The supplied sources contain no English route names. These names are curated
# translations/transliterations of their Myanmar route labels, with variants
# made explicit so that distinct services are not accidentally collapsed.
ROUTE_NAME_EN = {
    "1": "Hlegu Market – Zawana",
    "2": "Yuzana (Khine Shwe War Road) – Aung Mingalar Highway Bus Station",
    "3A": "Yuzana Garden City – 50th Street (via Tamwe)",
    "3B": "Yuzana Garden City – 50th Street (via Thuwunna Market)",
    "4": "Yuzana Garden City – Sule",
    "5": "Yoma Yeiktha – Bogyoke Aung San Road",
    "6A": "South Dagon (Thein Chaung) – Hlaing Tharyar",
    "6B": "South Dagon (70/71 Market) – Hlaing Tharyar",
    "7A": "South Dagon (70/72 Ward) – Maha Bandula Road (via Industrial Zone 2)",
    "7B": "South Dagon (70/72 Ward) – Maha Bandula Road (via Maungmakan Road)",
    "8": "Lanmadaw – South Dagon Inwa Housing",
    "9": "National Races Technological University – Kyauk Taing",
    "10": "National Races Village – Dagon University",
    "11": "Aung Mingalar Highway Bus Station – Shwedagon Pagoda",
    "12": "East Dagon – Sule",
    "13": "Parami – Botahtaung Pagoda",
    "14": "Parami (Nyaung Pin) – Thakhin Mya Park",
    "15-BoHmuBaHtoo": "Dagon University – Danyingone (via Bo Hmu Ba Htoo and Pyay Roads)",
    "15-BoHmuBaHtooBayintNaung": "Dagon University – Danyingone (via Bo Hmu Ba Htoo and Bayint Naung Roads)",
    "15-ShwePaukKan": "Dagon University – Danyingone (via Shwe Pauk Kan and Bayint Naung Road)",
    "16A": "Shwe Pauk Kan – Dagon Ayar Highway Bus Station (via Taungoo Road)",
    "16B": "Shwe Pauk Kan – Dagon Ayar Highway Bus Station (via Bo Tay Za Road)",
    "16C": "Aung Mingalar – Dagon Ayar Highway Bus Station",
    "17": "Shwe Pauk Kan – West Yangon Technological University",
    "18": "Khayay Yeik Mon – Zawana",
    "19": "Shwe Pauk Kan – Thakhin Mya Park",
    "20": "Dagon Ayar Highway Bus Station – Thakhin Mya Park (via Merchant Road)",
    "21": "West Yangon University (Htantabin) – Maha Bandula Road",
    "22": "West Yangon University (Htantabin) – Thakhin Mya Park",
    "23A": "Toe Chaung – Thakhin Mya Park (via Bayint Naung Bridge)",
    "23B": "Toe Chaung – Thakhin Mya Park (via Hlaing River Road)",
    "24A": "Kyan Sit Thar Road – Botahtaung Pagoda Road",
    "24B": "Dagon University – Botahtaung Pagoda Road",
    "25": "Dagon University – Mingalar Market",
    "26": "Dagon University – Botahtaung Pagoda Road",
    "27": "Mental Health Hospital – Kyaikkasan Road",
    "28": "Dagon University – Sule City Hall",
    "29": "Dagon University – Sule",
    "30-Pyay": "Dagon University – Thakhin Mya Park (via Pyay Road)",
    "30-Thamine": "Dagon University – Thakhin Mya Park (via Thamine)",
    "31": "Thanlyin (East Yangon University) – Botahtaung Market Road",
    "32": "Myanmar Maritime University – Htauk Kyant",
    "33": "Kyauktan – Yuzana Plaza",
    "34": "Khayan – Maha Bandula Road",
    "35": "Htauk Kyant – Maha Bandula Road",
    "36-AungMingalar": "Aung Mingalar – Sule",
    "36-HtaukKyant": "Htauk Kyant – Sule",
    "36-ShwePaukKan": "Shwe Pauk Kan – Sule",
    "37-Hlegu": "Sule – Hlegu",
    "37-Hmawbi": "Sule – Hmawbi",
    "37-HtaukKyant": "Sule – Htauk Kyant",
    "37-Okekan": "Sule – Okkan",
    "37-Waryarlatt": "Sule – Waryarlat",
    "38": "Parami (Nyaung Pin) – New Thiri Mingalar Market",
    "39": "Shwepyitha (Lein Kone) – Maha Bandula Road",
    "40": "Shwepyitha (Lein Kone) – Thakhin Mya Park",
    "41": "Htauk Kyant – Thakhin Mya Park",
    "42": "Shwepyitha (Lein Kone) – Yadanar Road",
    "43": "Waryarlat – Botahtaung Pagoda",
    "44": "Lein Kone – Hlegu Market",
    "45": "Hlegu Market – Min Kone",
    "46": "Dah Pein – South/North Junction",
    "47": "Hlaing Tharyar BOC – Twante",
    "48": "Dala – Twante",
    "49": "Hlaing Tharyar BOC – Kungyangon",
    "50": "Dala – Kungyangon",
    "51": "Bago – Khayan",
    "52": "Htantabin – Mee Khwet Market",
    "53": "Shwe Lin Ban Junction Circular",
    "54": "Gate 86 Circular",
    "55": "Parami – Thakhin Mya Park (via Sawbwagyigone)",
    "56": "Downtown Circular 56",
    "57": "Downtown Circular 57",
    "58": "Downtown Circular 58",
    "59": "South Dagon Thein Kyaung Junction – Central Women's Hospital",
    "60": "Yuzana Garden City – Kyauk Kone (Large Service)",
    "60-Mini": "South Dagon – Kyauk Kone (Mini Service)",
    "61": "West Yangon Technological University – Sule",
    "62": "Dagon University – Kyeemyindaing",
    "63": "San Pya Market – Thanlyet Soon",
    "64A": "Waibargi – Nan Thi Da Ferry Terminal (via Thudhamma Road)",
    "64B": "Waibargi – Nan Thi Da Ferry Terminal (via Khay Mar Thi Road)",
    "65A": "Botahtaung Pagoda – Shwepyitha (via Pale Road)",
    "65B": "Botahtaung Pagoda – Shwepyitha (via Bogyoke Aung San Road)",
    "66": "University of Computer Studies – Mental Health Hospital",
    "67": "Nyaung Shwe Circular",
    "68": "Shwepyitha (Ein Mae Gyi) – Technological University",
    "69": "Shwepyitha (Auk Seik) – Dagon Ayar Highway Bus Station",
    "70": "South Dagon – Kyauk Kone",
    "71": "Thayet Pin Chaung – San Pya Market",
    "72": "Ayarwon – Sule",
    "73": "Shwepyitha – Htauk Kyant",
    "74": "Shwepyitha – Dagon Ayar Highway Bus Station",
    "75": "Thuwunna Pagoda – Kyeemyindaing",
    "76": "East Yangon University – Industrial Zone 1",
    "77": "U Htaung Bo – Myin Hle Gate",
    "78": "University of Computer Studies – Sule (Yangon Central Railway Station)",
    "79": "Lin Sadaung – West Yangon University",
    "80-KhineShweWar": "Thakhin Mya Park – Yadanar Hnin Si Housing (via Khine Shwe War)",
    "80-Mini": "Upper Pansodan – Thaketa (Mini Service)",
    "80-MyinThawTar": "Thakhin Mya Park – Yadanar Hnin Si Housing (via Myin Taw Thar)",
    "81": "South/North Junction – Pansodan",
    "83": "Dagon Ayar Highway Bus Station – Inwa Housing",
    "84": "Thaketa – North Dagon",
    "85": "Thaketa – TB Hospital",
    "86": "Tamwe – Insein",
    "87-MaharMyaing": "Dagon University – Sule (via Mahar Myaing)",
    "87-MaWaTa": "Dagon University – Sule (via Ma Wa Ta)",
    "88": "Dagon University – Danyingone",
    "89-MinNanda": "Ayarwon – Pan Pin Gyi (via Min Nanda Road)",
    "89-MyinTawThar": "Ayarwon – Pan Pin Gyi (via Myin Taw Thar)",
    "90": "Okkan – Thakhin Mya Park",
    "91": "Taikkyi – No. 3 Road Junction",
    "92-KhayMarThi": "No. 3 Road Junction – Zawana (via Khay Mar Thi Road)",
    "92-Thudhamma": "No. 3 Road Junction – Zawana (via Thudhamma Road)",
    "93": "West Yangon University – Yangon Central Railway Station",
    "94": "University of Computer Studies – Yangon Central Railway Station",
    "95": "Kyauktan – Workers' Hospital",
    "96": "Hlawga Junction – Thaketa",
    "97": "Yangon University of Economics (Ywar Thar Gyi Campus) – Htauk Kyant",
    "98": "Dagon Ayar Highway Bus Station – Botahtaung (via Upper Kyeemyindaing Road)",
    "99": "Dagon Ayar Highway Bus Station – Shwe Li Road (Shwe Li Housing)",
    "100": "Min Ye Kyaw Swar Road – Botahtaung",
    "APS-Kabaraye": "Yangon Airport – Sule Loop (Kabar Aye outbound, Pyay Road inbound)",
    "APS-Pyay": "Yangon Airport – Sule Loop (Pyay Road outbound, Kabar Aye inbound)",
}


MYANMAR_TO_ASCII_DIGITS = str.maketrans("၀၁၂၃၄၅၆၇၈၉", "0123456789")


def clean_display(value: Any) -> str:
    text = unicodedata.normalize("NFC", str(value or ""))
    text = text.replace("\ufeff", "").replace("\u200b", "")
    return " ".join(text.split()).strip()


def normalize_text(value: Any) -> str:
    text = unicodedata.normalize("NFKC", str(value or "")).translate(
        MYANMAR_TO_ASCII_DIGITS
    )
    text = text.casefold().strip()
    return "".join(ch for ch in text if ch.isalnum())


def numeric_id_key(value: str) -> tuple[int, int | str, str]:
    if value.isdigit():
        return (0, int(value), value)
    return (1, value.casefold(), value)


def route_id_key(value: str) -> tuple[int, int, str]:
    match = re.match(r"^(\d+)", value)
    if match:
        return (0, int(match.group(1)), value.casefold())
    return (1, 10**9, value.casefold())


def bus_number(route_id: str) -> str:
    if route_id.startswith("APS-"):
        return "Airport Shuttle"
    match = re.match(r"^(\d+)", route_id)
    if match:
        return match.group(1)
    return route_id


def css_color(value: Any) -> str:
    color = str(value or "").strip().lstrip("#").upper()
    if not re.fullmatch(r"[0-9A-F]{6}", color):
        raise ValueError(f"Invalid route color: {value!r}")
    return f"#{color}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def find_member(archive: zipfile.ZipFile, suffix: str) -> str:
    matches = [name for name in archive.namelist() if name.replace("\\", "/").endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"Expected one ZIP member ending in {suffix!r}; found {matches}")
    return matches[0]


def read_zip_json(archive: zipfile.ZipFile, suffix: str) -> Any:
    member = find_member(archive, suffix)
    return json.loads(archive.read(member).decode("utf-8-sig"))


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = phi2 - phi1
    d_lng = math.radians(lng2 - lng1)
    h = math.sin(d_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lng / 2) ** 2
    return 2 * 6_371_000 * math.asin(math.sqrt(h))


def shape_endpoint_metrics(
    source_route: dict[str, Any],
    stop_sequence: list[str],
    stops: dict[str, dict[str, Any]],
) -> tuple[list[float], float] | None:
    coordinates = source_route.get("shape", {}).get("geometry", {}).get("coordinates", [])
    if len(coordinates) < 2 or not stop_sequence:
        return None

    endpoint_gaps = []
    for lng, lat in (coordinates[0], coordinates[-1]):
        endpoint_gaps.append(
            min(
                haversine_m(
                    float(lat),
                    float(lng),
                    stops[stop_id]["lat"],
                    stops[stop_id]["lng"],
                )
                for stop_id in stop_sequence
            )
        )

    first_lng, first_lat = coordinates[0]
    last_lng, last_lat = coordinates[-1]
    endpoint_separation = haversine_m(
        float(first_lat), float(first_lng), float(last_lat), float(last_lng)
    )
    return endpoint_gaps, endpoint_separation


def load_newer_source(path: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"CRC failure in {path}: {bad}")

        stops_member = find_member(archive, "/data/stops.tsv")
        reader = csv.DictReader(
            io.StringIO(archive.read(stops_member).decode("utf-8-sig")), delimiter="\t"
        )
        stops: dict[str, dict[str, Any]] = {}
        for row in reader:
            stop_id = str(row["id"]).strip()
            if stop_id in stops:
                raise ValueError(f"Duplicate stop ID in newer source: {stop_id}")
            stops[stop_id] = {
                "name_mm": clean_display(row["name_mm"]),
                "name_en": clean_display(row["name_en"]),
                "lat": float(row["lat"]),
                "lng": float(row["lng"]),
                "road_en": clean_display(row.get("road_en", "")),
                "road_mm": clean_display(row.get("road_mm", "")),
                "township_en": clean_display(row.get("township_en", "")),
                "township_mm": clean_display(row.get("township_mm", "")),
            }

        route_members = [
            name
            for name in archive.namelist()
            if re.search(r"/data/routes/[^/]+\.json$", name.replace("\\", "/"))
        ]
        routes = [json.loads(archive.read(name).decode("utf-8-sig")) for name in route_members]
    return stops, routes


def load_legacy_source(path: Path) -> dict[str, Any]:
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"CRC failure in {path}: {bad}")
        return {
            "stops": read_zip_json(archive, "/bus-stop-data-by-id.js"),
            "lines": read_zip_json(archive, "/bus-line-data-by-id.js"),
            "line_stop_ids": read_zip_json(archive, "/bus-stop-ids-of-lines.js"),
            "line_stop_names": read_zip_json(archive, "/bus-stop-names-of-lines.js"),
        }


def exact_duplicate_groups(stops: dict[str, dict[str, Any]]) -> list[list[str]]:
    groups: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for stop_id, stop in stops.items():
        signature = (
            normalize_text(stop["name_mm"]),
            normalize_text(stop["name_en"]),
            round(float(stop["lat"]), 7),
            round(float(stop["lng"]), 7),
        )
        groups[signature].append(stop_id)
    return [sorted(ids, key=numeric_id_key) for ids in groups.values() if len(ids) > 1]


def legacy_duplicate_groups(stops: dict[str, dict[str, Any]]) -> list[list[str]]:
    groups: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for stop_id, stop in stops.items():
        geo = stop["geo"]
        signature = (
            normalize_text(stop.get("name")),
            normalize_text(stop.get("label")),
            normalize_text(stop.get("road")),
            normalize_text(stop.get("township")),
            round(float(geo[1]), 7),
            round(float(geo[0]), 7),
        )
        groups[signature].append(str(stop_id))
    return [sorted(ids, key=numeric_id_key) for ids in groups.values() if len(ids) > 1]


def build_master(
    newer_stops: dict[str, dict[str, Any]],
    newer_routes: list[dict[str, Any]],
    legacy: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    legacy_stops: dict[str, dict[str, Any]] = legacy["stops"]
    legacy_lines: dict[str, dict[str, Any]] = legacy["lines"]

    newer_ids = set(newer_stops)
    legacy_ids = set(legacy_stops)
    common_ids = newer_ids & legacy_ids

    coordinate_differences: list[float] = []
    myanmar_name_differences = 0
    for stop_id in common_ids:
        current = newer_stops[stop_id]
        old = legacy_stops[stop_id]
        distance = haversine_m(
            current["lat"], current["lng"], float(old["geo"][1]), float(old["geo"][0])
        )
        coordinate_differences.append(distance)
        legacy_name = old.get("label") or old.get("name") or ""
        if normalize_text(current["name_mm"]) != normalize_text(legacy_name):
            myanmar_name_differences += 1

    # Prefer the newer bilingual source for common IDs. It is a strict superset
    # in the supplied files. A legacy-only record would be retained, but the
    # build rejects it if no truthful English name is available.
    combined_stops = {stop_id: dict(stop) for stop_id, stop in newer_stops.items()}
    legacy_only_ids = sorted(legacy_ids - newer_ids, key=numeric_id_key)
    for stop_id in legacy_only_ids:
        old = legacy_stops[stop_id]
        combined_stops[stop_id] = {
            "name_mm": clean_display(old.get("label") or old.get("name") or ""),
            "name_en": "",
            "lat": float(old["geo"][1]),
            "lng": float(old["geo"][0]),
            "road_en": "",
            "road_mm": clean_display(old.get("road") or ""),
            "township_en": "",
            "township_mm": clean_display(old.get("township") or ""),
        }
    if any(not stop["name_en"] for stop in combined_stops.values()):
        missing = [stop_id for stop_id, stop in combined_stops.items() if not stop["name_en"]]
        raise ValueError(f"Cannot truthfully populate name_en for stops: {missing}")

    exact_duplicate_stop_candidates = exact_duplicate_groups(combined_stops)
    cooccurring_duplicate_stop_groups: list[list[str]] = []
    for group in exact_duplicate_stop_candidates:
        group_ids = set(group)
        cooccurs = any(
            len(group_ids & {str(stop_id) for stop_id in route.get("stops", [])}) > 1
            for route in newer_routes
        )
        if cooccurs:
            cooccurring_duplicate_stop_groups.append(group)

    # The target schema describes physical stops and has no platform/direction
    # attributes. Exact-equal records are therefore merged even when both IDs
    # appear on opposite route legs; the canonical ID remains at both sequence
    # positions, preserving travel order.
    duplicate_stop_groups = exact_duplicate_stop_candidates

    stop_aliases: dict[str, str] = {stop_id: stop_id for stop_id in combined_stops}
    for group in duplicate_stop_groups:
        canonical = group[0]
        for duplicate in group[1:]:
            stop_aliases[duplicate] = canonical

    final_stops: dict[str, dict[str, Any]] = {}
    for stop_id in sorted(combined_stops, key=numeric_id_key):
        if stop_aliases[stop_id] != stop_id:
            continue
        stop = combined_stops[stop_id]
        final_stops[stop_id] = {
            "name_mm": stop["name_mm"],
            "name_en": stop["name_en"],
            "lat": stop["lat"],
            "lng": stop["lng"],
        }

    source_route_ids = {str(route["route_id"]) for route in newer_routes}
    source_route_by_id = {str(route["route_id"]): route for route in newer_routes}
    translation_ids = set(ROUTE_NAME_EN)
    if source_route_ids != translation_ids:
        raise ValueError(
            "English route-name table does not match source IDs; "
            f"missing={sorted(source_route_ids - translation_ids, key=route_id_key)}, "
            f"extra={sorted(translation_ids - source_route_ids, key=route_id_key)}"
        )

    candidate_routes: dict[str, dict[str, Any]] = {}
    consecutive_alias_collapses = 0
    for route in newer_routes:
        route_id = str(route["route_id"])
        if route_id in candidate_routes:
            raise ValueError(f"Duplicate route ID in newer source: {route_id}")

        mapped_sequence: list[str] = []
        previous_source_stop_id: str | None = None
        for source_stop_id in route.get("stops", []):
            source_stop_id = str(source_stop_id)
            if source_stop_id not in stop_aliases:
                raise ValueError(f"Route {route_id} references missing stop {source_stop_id}")
            canonical = stop_aliases[source_stop_id]
            if (
                mapped_sequence
                and mapped_sequence[-1] == canonical
                and previous_source_stop_id != source_stop_id
            ):
                consecutive_alias_collapses += 1
                previous_source_stop_id = source_stop_id
                continue
            mapped_sequence.append(canonical)
            previous_source_stop_id = source_stop_id

        route_color = route.get("color")
        number = bus_number(route_id)
        legacy_color = None
        if number in legacy_lines:
            legacy_color = legacy_lines[number].get("station", {}).get("color")
        if not route_color and legacy_color:
            route_color = legacy_color

        candidate_routes[route_id] = {
            "bus_number": number,
            "bus_color": css_color(route_color),
            "name_en": ROUTE_NAME_EN[route_id],
            "stop_sequence": mapped_sequence,
        }

    pre_quarantine_sequence_groups: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for route_id, route in candidate_routes.items():
        sequence = tuple(route["stop_sequence"])
        if sequence:
            pre_quarantine_sequence_groups[sequence].append(route_id)
    source_sequence_collisions = [
        sorted(ids, key=route_id_key)
        for ids in pre_quarantine_sequence_groups.values()
        if len(ids) > 1
    ]

    active_route_quarantine: dict[str, str] = {}
    for route_id, route in candidate_routes.items():
        if len(route["stop_sequence"]) < 2:
            active_route_quarantine[route_id] = (
                "No usable ordered stop sequence is present in the supplied archives."
            )

    collision_resolution_evidence: dict[str, Any] = {}
    if "46" in candidate_routes and "71" in candidate_routes:
        route_46_sequence = candidate_routes["46"]["stop_sequence"]
        route_71_sequence = candidate_routes["71"]["stop_sequence"]
        metrics_46 = shape_endpoint_metrics(
            source_route_by_id["46"], route_46_sequence, final_stops
        )
        metrics_71 = shape_endpoint_metrics(
            source_route_by_id["71"], route_71_sequence, final_stops
        )
        if (
            route_46_sequence
            and route_46_sequence == route_71_sequence
            and metrics_46 is not None
            and metrics_71 is not None
            and max(metrics_46[0]) > 10_000
            and max(metrics_71[0]) < 500
        ):
            active_route_quarantine["46"] = (
                "Its sequence duplicates route 71 and omits over 10 km of route 46's own open GeoJSON path."
            )
            collision_resolution_evidence["46_vs_71"] = {
                "shared_ordered_sequence": True,
                "kept_route_id": "71",
                "quarantined_route_id": "46",
                "route_46_shape_endpoint_to_nearest_sequence_stop_m": [
                    round(gap, 1) for gap in metrics_46[0]
                ],
                "route_71_shape_endpoint_to_nearest_sequence_stop_m": [
                    round(gap, 1) for gap in metrics_71[0]
                ],
            }

    active_route_quarantine = {
        route_id: active_route_quarantine[route_id]
        for route_id in sorted(active_route_quarantine, key=route_id_key)
    }

    eligible_routes = {
        route_id: route
        for route_id, route in candidate_routes.items()
        if route_id not in active_route_quarantine
    }

    # A route is a true duplicate only when its displayed service identity,
    # curated name, and canonical ordered sequence all agree. Distinct valid
    # variants are intentionally preserved.
    route_identity_groups: dict[tuple[Any, ...], list[str]] = defaultdict(list)
    for route_id, route in eligible_routes.items():
        key = (
            normalize_text(route["bus_number"]),
            normalize_text(route["name_en"]),
            tuple(route["stop_sequence"]),
        )
        route_identity_groups[key].append(route_id)
    duplicate_route_groups = [
        sorted(ids, key=route_id_key) for ids in route_identity_groups.values() if len(ids) > 1
    ]
    removed_route_ids = {route_id for group in duplicate_route_groups for route_id in group[1:]}
    final_routes = {
        route_id: eligible_routes[route_id]
        for route_id in sorted(eligible_routes, key=route_id_key)
        if route_id not in removed_route_ids
    }

    ordered_sequence_collisions: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for route_id, route in final_routes.items():
        sequence = tuple(route["stop_sequence"])
        if sequence:
            ordered_sequence_collisions[sequence].append(route_id)
    remaining_same_sequence_distinct_services = [
        sorted(ids, key=route_id_key)
        for ids in ordered_sequence_collisions.values()
        if len(ids) > 1
    ]

    same_name_nearby_pairs = 0
    stop_items = list(combined_stops.items())
    for index, (_, left) in enumerate(stop_items):
        for _, right in stop_items[index + 1 :]:
            if normalize_text(left["name_mm"]) != normalize_text(right["name_mm"]):
                continue
            if normalize_text(left["name_en"]) != normalize_text(right["name_en"]):
                continue
            if abs(left["lat"] - right["lat"]) > 0.0003 or abs(left["lng"] - right["lng"]) > 0.0003:
                continue
            if haversine_m(left["lat"], left["lng"], right["lat"], right["lng"]) <= 25:
                same_name_nearby_pairs += 1

    legacy_route_ids = set(legacy_lines)
    exact_route_id_overlap = source_route_ids & legacy_route_ids
    color_disagreements = []

    suspected_partial_route_sequences: dict[str, dict[str, Any]] = {}
    endpoint_gap_review_threshold_m = 1_000
    for route_id, route in final_routes.items():
        source_route = source_route_by_id[route_id]
        metrics = shape_endpoint_metrics(
            source_route, route["stop_sequence"], final_stops
        )
        if metrics is None:
            continue
        endpoint_gaps, shape_endpoint_separation = metrics
        if (
            shape_endpoint_separation > endpoint_gap_review_threshold_m
            and max(endpoint_gaps) > endpoint_gap_review_threshold_m
        ):
            suspected_partial_route_sequences[route_id] = {
                "shape_endpoint_to_nearest_sequence_stop_m": [
                    round(gap, 1) for gap in endpoint_gaps
                ],
                "shape_endpoint_separation_m": round(shape_endpoint_separation, 1),
                "reason": "The open GeoJSON shape has an endpoint over 1 km from every supplied sequence stop.",
            }

    for route_id in sorted(exact_route_id_overlap, key=route_id_key):
        old_color = legacy_lines[route_id].get("station", {}).get("color")
        if old_color and css_color(old_color) != css_color(source_route_by_id[route_id]["color"]):
            color_disagreements.append(route_id)

    report = {
        "source_comparison": {
            "newer_stop_count": len(newer_stops),
            "legacy_stop_count": len(legacy_stops),
            "common_stop_ids": len(common_ids),
            "newer_only_stop_ids": len(newer_ids - legacy_ids),
            "legacy_only_stop_ids": len(legacy_only_ids),
            "common_ids_with_coordinate_change_over_1m": sum(
                distance > 1 for distance in coordinate_differences
            ),
            "common_ids_with_coordinate_change_over_25m": sum(
                distance > 25 for distance in coordinate_differences
            ),
            "maximum_common_id_coordinate_change_m": round(max(coordinate_differences), 3),
            "common_ids_with_myanmar_label_difference": myanmar_name_differences,
            "newer_route_count": len(newer_routes),
            "legacy_route_metadata_count": len(legacy_lines),
            "exact_route_id_overlap": len(exact_route_id_overlap),
            "route_color_disagreements": color_disagreements,
            "legacy_route_id_arrays_used_as_sequences": False,
            "legacy_sequence_reason": "The arrays are numerically sorted membership sets, not travel order.",
        },
        "deduplication": {
            "exact_coordinate_and_bilingual_name_candidates": exact_duplicate_stop_candidates,
            "merged_stop_groups": duplicate_stop_groups,
            "merged_stop_groups_with_route_cooccurrence": cooccurring_duplicate_stop_groups,
            "stop_id_aliases": {
                stop_id: canonical
                for stop_id, canonical in stop_aliases.items()
                if stop_id != canonical
            },
            "legacy_exact_duplicate_groups_superseded_by_newer_source": legacy_duplicate_groups(
                legacy_stops
            ),
            "same_bilingual_name_pairs_within_25m_found": same_name_nearby_pairs,
            "nonidentical_nearby_pairs_preserved_as_potential_directional_stops": True,
            "consecutive_route_entries_collapsed_after_stop_merge": consecutive_alias_collapses,
            "removed_true_duplicate_route_groups": duplicate_route_groups,
            "source_same_sequence_groups_found": source_sequence_collisions,
            "remaining_same_sequence_distinct_service_ids": remaining_same_sequence_distinct_services,
        },
        "output": {
            "stop_count": len(final_stops),
            "route_count": len(final_routes),
            "quarantined_source_routes": active_route_quarantine,
            "route_sequence_collision_resolution": collision_resolution_evidence,
            "shape_endpoint_gap_review_threshold_m": endpoint_gap_review_threshold_m,
            "suspected_partial_route_sequences": suspected_partial_route_sequences,
            "english_route_names": "Curated from the supplied Myanmar labels and bilingual stop catalog.",
        },
    }
    return {"stops": final_stops, "routes": final_routes}, report


def validate_master(master: dict[str, Any]) -> dict[str, Any]:
    if list(master) != ["stops", "routes"]:
        raise ValueError("Top-level schema must contain only stops and routes, in that order")

    expected_stop_keys = ["name_mm", "name_en", "lat", "lng"]
    for stop_id, stop in master["stops"].items():
        if list(stop) != expected_stop_keys:
            raise ValueError(f"Invalid stop schema for {stop_id}: {list(stop)}")
        if not stop["name_mm"] or not stop["name_en"]:
            raise ValueError(f"Blank stop name for {stop_id}")
        if not isinstance(stop["lat"], (int, float)) or not isinstance(stop["lng"], (int, float)):
            raise ValueError(f"Nonnumeric coordinates for {stop_id}")
        if not (15 <= stop["lat"] <= 18.5 and 94 <= stop["lng"] <= 98):
            raise ValueError(f"Out-of-region coordinates for {stop_id}: {stop}")

    expected_route_keys = ["bus_number", "bus_color", "name_en", "stop_sequence"]
    missing_references: list[tuple[str, str]] = []
    for route_id, route in master["routes"].items():
        if list(route) != expected_route_keys:
            raise ValueError(f"Invalid route schema for {route_id}: {list(route)}")
        if not route["bus_number"] or not route["name_en"]:
            raise ValueError(f"Blank route field for {route_id}")
        if not re.fullmatch(r"#[0-9A-F]{6}", route["bus_color"]):
            raise ValueError(f"Invalid CSS color for {route_id}: {route['bus_color']}")
        if not isinstance(route["stop_sequence"], list):
            raise ValueError(f"stop_sequence is not an array for {route_id}")
        if len(route["stop_sequence"]) < 2:
            raise ValueError(f"Route {route_id} has fewer than two ordered stops")
        for stop_id in route["stop_sequence"]:
            if not isinstance(stop_id, str):
                raise ValueError(f"Non-string stop ID in route {route_id}: {stop_id!r}")
            if stop_id not in master["stops"]:
                missing_references.append((route_id, stop_id))
    if missing_references:
        raise ValueError(f"Missing stop references: {missing_references}")

    duplicate_final_stops = exact_duplicate_groups(master["stops"])
    if duplicate_final_stops:
        raise ValueError(f"Unresolved duplicate stop records remain: {duplicate_final_stops}")

    return {
        "schema_valid": True,
        "all_route_stop_references_resolve": True,
        "unresolved_duplicate_final_stop_groups": [],
        "stop_count": len(master["stops"]),
        "route_count": len(master["routes"]),
        "route_stop_reference_count": sum(
            len(route["stop_sequence"]) for route in master["routes"].values()
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--newer-archive", type=Path, default=DEFAULT_NEWER_ARCHIVE)
    parser.add_argument("--legacy-archive", type=Path, default=DEFAULT_LEGACY_ARCHIVE)
    parser.add_argument("--output", type=Path, default=Path("ybs_data.json"))
    parser.add_argument("--report", type=Path, default=Path("ybs_merge_report.json"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    for path in (args.newer_archive, args.legacy_archive):
        if not path.is_file():
            raise FileNotFoundError(path)

    newer_stops, newer_routes = load_newer_source(args.newer_archive)
    legacy = load_legacy_source(args.legacy_archive)
    master, report = build_master(newer_stops, newer_routes, legacy)
    validation = validate_master(master)

    report["inputs"] = {
        "newer_archive": str(args.newer_archive.resolve()),
        "newer_archive_sha256": sha256(args.newer_archive),
        "legacy_archive": str(args.legacy_archive.resolve()),
        "legacy_archive_sha256": sha256(args.legacy_archive),
    }
    report["validation"] = validation

    master_json = json.dumps(master, ensure_ascii=False, indent=2) + "\n"
    master_bytes = master_json.encode("utf-8")
    report["output"]["master_sha256"] = hashlib.sha256(
        master_bytes
    ).hexdigest().upper()
    report["output"]["master_size_bytes"] = len(master_bytes)

    args.output.write_bytes(master_bytes)
    args.report.write_bytes(
        (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )

    print(
        json.dumps(
            {
                "output": str(args.output.resolve()),
                "report": str(args.report.resolve()),
                **validation,
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise
