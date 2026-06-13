# Hex Map Data Formats

This note records the difference between the data formats used by the UK AQ hex maps.

## JSON

**JSON** is the general-purpose data format: JavaScript Object Notation.

A `.json` file can contain almost any structured data: arrays, objects, strings, numbers, booleans, and null values.

GeoJSON and HexJSON are both JSON-based formats, but they have more specific conventions.

```text
JSON = general data format
GeoJSON = JSON with a geospatial FeatureCollection structure
HexJSON = JSON with a hex-cartogram grid structure
```

## GeoJSON

**GeoJSON** is a standard JSON format for map geometry.

It normally stores data as a `FeatureCollection`, containing one or more `Feature` objects. Each feature has:

- `properties`: metadata such as local authority code, name, group, or region
- `geometry`: polygon or multipolygon coordinates

Example shape:

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "la_code": "W06000015",
        "la_name": "Cardiff",
        "region_nation": "Wales"
      },
      "geometry": {
        "type": "MultiPolygon",
        "coordinates": []
      }
    }
  ]
}
```

GeoJSON is a good fit for the Countries & Regions local-authority map because one local authority can be represented by multiple joined hexes inside a single feature.

## HexJSON

**HexJSON** is a JSON-based format for hex cartograms.

Instead of storing full polygon geometry, it normally stores hex-grid positions. It is most useful when each area is represented by one regular hex cell.

Example shape:

```json
{
  "layout": "odd-r",
  "hexes": {
    "E14001123": {
      "q": 10,
      "r": 12,
      "n": "Example constituency"
    }
  }
}
```

HexJSON is compact and convenient for regular one-area-per-hex cartograms, but it is less convenient where one area needs multiple joined hex cells unless extra grouping logic is added.

## UK AQ website usage

The UK AQ website currently uses different formats for the two hex-map modes.

### UK tab

The UK / Westminster constituency view uses **HexJSON** files:

```text
data/PCON/uk-constituencies-2023.hexjson
data/PCON/uk-constituencies-2017.hexjson
```

These files are genuinely HexJSON, so the `.hexjson` suffix is appropriate.

### Countries & Regions tab

The Countries & Regions local-authority view uses a **GeoJSON-style FeatureCollection** file:

```text
data/LAD/uk_aq_la_hex_2025.geojson
```

This file uses a GeoJSON-style structure: `FeatureCollection` → `Feature` → `properties` + `geometry`. The `.geojson` suffix reflects this. The browser loads it with `response.json()` because GeoJSON is valid JSON.

## Practical rule

Use:

```text
.hexjson  for constituency hex-cartogram files
.geojson  for local-authority polygon/multipolygon hex geometry
.json     for general non-map data
```

For the Wales local-authority override, use a GeoJSON-style file such as:

```text
data/LAD/uk_aq_la_wales_hex_custom_2025.geojson
```

This keeps the source format clear and avoids confusing general JSON, GeoJSON, and HexJSON.
