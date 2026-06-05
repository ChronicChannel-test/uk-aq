Codex prompt:

Please investigate why the AQI coloured bands in hex_map.html chart mode are not displaying the R2 History AQI Levels correctly.

Do not implement a fix yet.

I want an investigation report and fix options first. The fix options should include pros, cons, recommendations, and the likely effect on R2 read/write access limits.

Context:
hex_map.html has chart mode with selected sensor time-series lines. It should also show AQI coloured bands for DAQI and EAQI. These bands should come from the R2 History AQI Levels, not from a rough client-side recalculation.

Please inspect the complete AQI band pipeline in hex_map.html, including but not limited to:

- AQI history endpoint/base URL configuration
- aqiHistoryBaseCandidates
- buildAqiHistoryRequestCandidates
- fetchAqiBands
- parseAqiBandPayload
- aqiBandCache
- getCachedAqiPoints
- prefetchAqiBandsForEntries
- renderAqiBands
- chart mode update/render functions that pass aqiPoints
- selected AQI source sensor logic
- pollutant switching logic
- chart range switching logic

Please trace the intended data flow:

1. User opens chart mode from a hex.
2. Chart selects up to four sensors.
3. One selected sensor is used as the AQI band source.
4. The selected pollutant and chart range are used to request hourly AQI history.
5. The AQI history endpoint reads R2 History AQI Levels.
6. The frontend parses DAQI and EAQI levels.
7. The chart renders DAQI and EAQI coloured bands across the x-axis domain.

Please check whether each step is actually happening.

Things to verify:

1. Endpoint calls
- Is the AQI history endpoint being called?
- What exact URL is used?
- Are multiple fallback URLs being tried?
- Are any fallback URLs stale or misleading?
- Is the final deployed route correct?

2. Request params
Check whether the frontend request params match the actual AQI history API handler and R2 key/query expectations.

Current frontend code appears to send params like:

- scope=timeseries
- grain=hourly
- timeseries_id
- entity
- pollutant
- row_limit
- from_utc
- to_utc

Please verify whether these are correct.

3. Identifier mismatch
Check whether timeseriesId is definitely the correct identifier for R2 AQI history.

If the backend/R2 history is keyed by another value, such as station ID, source ID, canonical timeseries key, source-specific ID, area ID, or another entity key, identify the mismatch clearly.

4. Response shape
Check whether parseAqiBandPayload matches the actual AQI history response shape.

Current frontend parsing appears to look for timestamp fields such as:

- period_start_utc
- timestamp_hour_utc
- observed_at

And pollutant-specific AQI fields such as:

PM2.5:
- daqi_pm25_rolling24h_index_level
- eaqi_pm25_index_level

PM10:
- daqi_pm10_rolling24h_index_level
- eaqi_pm10_index_level

NO2:
- daqi_no2_index_level
- eaqi_no2_index_level

Please verify whether the real response uses exactly these fields. If the real response uses different names or a nested/compact format, document that.

5. Cache behaviour
Check whether AQI band cache logic can incorrectly hide future fetch attempts.

In particular, check whether a failed request, empty response, malformed response, or field-name mismatch can still mark a time range as covered. If so, the chart may stop trying to fetch AQI bands even though none were successfully loaded.

6. Render behaviour
Check whether AQI data is fetched and parsed but not visible because of rendering issues.

Inspect:

- SVG group ordering
- clipping
- chart margins
- y positions
- whether DAQI/EAQI rows are outside the visible chart area
- whether rectangles are rendered with zero width
- whether colours are missing
- whether the x-domain does not overlap the AQI timestamps
- whether stale currentAqiPoints or existingAqiOnFrame logic is reusing empty data

7. Mode switching
Check whether AQI bands update correctly when:

- switching pollutant
- switching chart range
- switching selected AQI source chip
- opening chart mode from a different hex
- switching between United Kingdom/Constituencies and Countries & Regions/Local Authorities

8. Debugging
Add temporary debugging only if needed, and keep it behind a simple flag or URL param.

Suggested approach:

- ?debug_aqi=1
- or window.UK_AQ_DEBUG_AQI_BANDS = true

Debug output should show:

- selected AQI source sensor
- selected pollutant
- chart range
- requested AQI URL
- response status
- response row count
- parsed DAQI/EAQI point count
- cache hit/miss status
- render band count

Please do not leave noisy debug output enabled by default.

Deliverable:
Please produce a report before making any changes. The report should include:

A. Most likely root cause or causes  
B. Evidence from the code and, if possible, runtime/network behaviour  
C. Fix options  
D. Pros and cons for each option  
E. Recommended option  
F. R2 read/write access limit impact for each option  
G. Specific files/functions that would need changing  
H. Test plan  
I. Any decisions needed from me before implementation  

Fix options should include at least these categories, but you may add better ones if the codebase suggests them:

Option 1: Minimal frontend fix
Examples:
- correct endpoint URL
- correct request params
- correct field names in parser
- correct timestamp parsing
- correct rendering bug

Option 2: Harden the current frontend AQI-history client
Examples:
- one canonical endpoint
- better response-shape normalisation
- better error handling
- do not mark failed/empty ranges as covered
- request de-duplication
- debug flag
- clearer fallback behaviour

Option 3: Backend/API response adjustment
Examples:
- change the AQI history API to return exactly what the frontend needs
- preserve frontend contract
- make response stable across pollutants
- return DAQI and EAQI levels in a consistent compact format

Option 4: Merge AQI levels into the existing chart timeseries response
Examples:
- chart API returns observation points plus AQI band points together
- frontend does not make a separate AQI-history request for the selected AQI source sensor

Option 5: Precomputed compact AQI band objects in R2
Examples:
- write compact per-timeseries/per-pollutant AQI band strips
- fetch run-length encoded AQI segments for the selected range
- optimise for high public traffic later

Option 6: Development-only client-side fallback
Examples:
- calculate approximate bands from loaded observations only when R2 AQI history is unavailable
- only use this for debugging, not as the normal production display

For each option, include:

- what would change
- which files/functions are affected
- expected reliability
- expected implementation complexity
- risk of regressions
- R2 reads impact
- R2 writes impact
- whether it is suitable now or later

Important:
Do not choose a fix and implement it without reporting first.

I want the investigation and the options first, then I will decide which option to implement.