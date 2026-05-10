// chart-core.js — shared chart utilities for hex_map and sensors_chart.
// Plain IIFE. Does not depend on D3 at parse time; D3 is resolved lazily on first call.
(function () {
  var GAP_THRESHOLD_MS = 65 * 60 * 1000; // 65 minutes

  var SYMBOL_INTERVAL_MS = {
    "24h": 3 * 60 * 60 * 1000,        // every 3 h  → ~8 symbols
    "7d":  12 * 60 * 60 * 1000,       // every 12 h → ~14 symbols
    "31d": 3 * 24 * 60 * 60 * 1000,   // every 3 d  → ~10 symbols
    "90d": 7 * 24 * 60 * 60 * 1000,   // every 7 d  → ~13 symbols
  };

  var SYMBOL_GLYPHS = ["●", "■", "▲", "◆", "✚"];

  // SYMBOL_TYPES resolved lazily so D3 need not be present when this IIFE runs.
  var _symbolTypes = null;
  function resolveSymbolTypes() {
    if (!_symbolTypes) {
      _symbolTypes = [
        d3.symbolCircle,
        d3.symbolSquare,
        d3.symbolTriangle,
        d3.symbolDiamond,
        d3.symbolCross,
      ];
    }
    return _symbolTypes;
  }

  // buildSegments(points)
  // Splits an array of {date, value} points into contiguous segments wherever
  // the gap between consecutive points exceeds GAP_THRESHOLD_MS.
  // Points with non-finite .value are excluded entirely.
  // Returns an array of segment arrays, each sorted by ascending time.
  function buildSegments(points) {
    if (!Array.isArray(points) || !points.length) return [];
    var sorted = points.slice().sort(function (a, b) {
      return a.date.getTime() - b.date.getTime();
    });
    var valid = sorted.filter(function (p) {
      return Number.isFinite(p.value);
    });
    if (!valid.length) return [];
    var segments = [];
    var current = [valid[0]];
    for (var i = 1; i < valid.length; i++) {
      if (valid[i].date.getTime() - valid[i - 1].date.getTime() > GAP_THRESHOLD_MS) {
        segments.push(current);
        current = [];
      }
      current.push(valid[i]);
    }
    if (current.length) segments.push(current);
    return segments;
  }

  // getSymbolPositions(points, segments, intervalMs)
  // Returns a Set of indices (into the original points array) that should
  // receive a symbol marker.
  // Rules:
  //   1. First and last point of every segment are always included.
  //   2. Within each segment, mark a point if it is >= intervalMs since the
  //      last marked point (counting from the first point's time, not from a
  //      first-endpoint mark — the endpoint is always included regardless).
  //   3. Deduplication is automatic (Set).
  function getSymbolPositions(points, segments, intervalMs) {
    var result = new Set();
    if (!Array.isArray(points) || !Array.isArray(segments)) return result;

    // Build a map from point object → original index so segment references
    // can be traced back to original array positions.
    var indexByPoint = new Map();
    points.forEach(function (p, i) {
      indexByPoint.set(p, i);
    });

    segments.forEach(function (segment) {
      if (!segment.length) return;

      var firstIdx = indexByPoint.get(segment[0]);
      var lastIdx  = indexByPoint.get(segment[segment.length - 1]);
      if (firstIdx !== undefined) result.add(firstIdx);
      if (lastIdx  !== undefined) result.add(lastIdx);

      if (segment.length <= 2) return;

      // Walk interior points and mark by interval.
      // lastMarkedTime starts at the first point's time (interval counts from there).
      var lastMarkedTime = segment[0].date.getTime();
      for (var i = 1; i < segment.length - 1; i++) {
        var t = segment[i].date.getTime();
        if (t - lastMarkedTime >= intervalMs) {
          var idx = indexByPoint.get(segment[i]);
          if (idx !== undefined) {
            result.add(idx);
            lastMarkedTime = t;
          }
        }
      }
    });
    return result;
  }

  // getSymbolIntervalMs(windowValue)
  // Returns the ms interval for the given window string. Falls back to 3 h.
  function getSymbolIntervalMs(windowValue) {
    return SYMBOL_INTERVAL_MS[windowValue] || (3 * 60 * 60 * 1000);
  }

  // renderSeriesSymbols(svg, points, symbolPositionSet, xScale, yScale, symbolTypeIndex)
  // Appends D3 symbol <path> elements to the given SVG selection.
  function renderSeriesSymbols(svg, points, symbolPositionSet, xScale, yScale, symbolTypeIndex) {
    var symbolTypes = resolveSymbolTypes();
    var symType = symbolTypes[symbolTypeIndex % symbolTypes.length];
    var symGen = d3.symbol().type(symType).size(48);
    symbolPositionSet.forEach(function (idx) {
      var point = points[idx];
      if (!point || !Number.isFinite(point.value)) return;
      var x = xScale(point.date);
      var y = yScale(point.value);
      svg.append("path")
        .attr("d", symGen())
        .attr("transform", "translate(" + x + "," + y + ")")
        .attr("fill", "#3C78AC")
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.5)
        .style("pointer-events", "none");
    });
  }

  // renderProgressBar(svgEl, frame)
  // Creates a progress bar (two SVG rects) directly on svgEl (raw DOM element).
  // Returns { update(fraction), remove() }.
  function renderProgressBar(svgEl, frame) {
    var margin    = frame.margin;
    var plotWidth = frame.width - margin.left - margin.right;
    var y         = margin.top - 6;

    var NS = "http://www.w3.org/2000/svg";

    // Track (background)
    var track = document.createElementNS(NS, "rect");
    track.setAttribute("x",      String(margin.left));
    track.setAttribute("y",      String(y));
    track.setAttribute("width",  String(plotWidth));
    track.setAttribute("height", "4");
    track.setAttribute("fill",   "rgba(60, 120, 172, 0.15)");
    track.setAttribute("rx",     "2");
    svgEl.appendChild(track);

    // Fill (indicator, grows left-to-right from the right edge)
    var fill = document.createElementNS(NS, "rect");
    fill.setAttribute("x",      String(margin.left + plotWidth));
    fill.setAttribute("y",      String(y));
    fill.setAttribute("width",  "0");
    fill.setAttribute("height", "4");
    fill.setAttribute("fill",   "#3C78AC");
    fill.setAttribute("rx",     "2");
    fill.setAttribute("opacity", "0.8");
    fill.style.transition = "x 0.2s ease-out, width 0.2s ease-out";
    svgEl.appendChild(fill);

    return {
      update: function (loadedFraction) {
        var fraction    = Math.max(0, Math.min(1, loadedFraction));
        var filledWidth = plotWidth * fraction;
        fill.setAttribute("x",     String(margin.left + plotWidth * (1 - fraction)));
        fill.setAttribute("width", String(filledWidth));
      },
      remove: function () {
        track.style.transition = "opacity 0.3s ease";
        fill.style.transition  = "opacity 0.3s ease";
        track.style.opacity    = "0";
        fill.style.opacity     = "0";
        setTimeout(function () {
          if (track.parentNode) track.parentNode.removeChild(track);
          if (fill.parentNode)  fill.parentNode.removeChild(fill);
        }, 300);
      },
    };
  }

  // applyChunkFade(svgEl)
  // Briefly dims the SVG to signal that new data has arrived, then fades back.
  function applyChunkFade(svgEl) {
    svgEl.style.transition = "";
    svgEl.style.opacity    = "0.7";
    requestAnimationFrame(function () {
      svgEl.style.transition = "opacity 150ms ease-out";
      svgEl.style.opacity    = "1";
    });
  }

  window.ChartCore = {
    GAP_THRESHOLD_MS:    GAP_THRESHOLD_MS,
    SYMBOL_INTERVAL_MS:  SYMBOL_INTERVAL_MS,
    get SYMBOL_TYPES()   { return resolveSymbolTypes(); },
    SYMBOL_GLYPHS:       SYMBOL_GLYPHS,
    buildSegments:       buildSegments,
    getSegments:         buildSegments,        // convenience alias
    getSymbolPositions:  getSymbolPositions,
    getSymbolIntervalMs: getSymbolIntervalMs,
    renderSeriesSymbols: renderSeriesSymbols,
    renderProgressBar:   renderProgressBar,
    applyChunkFade:      applyChunkFade,
  };
})();
