---
title: AQI integrity checks
status: Planned
area: Data integrity
updated: 2026-05-24
---
Add checks to detect missing AQI levels where observations exist and AQI values should be present.

- Check for gaps in AQI levels where data appears incomplete.
- Compare days with observations against days where AQI values are expected.
- Report affected days, connectors, and sensors so issues can be reviewed quickly.
- Leave remediation options for a later task after visibility checks are established.
