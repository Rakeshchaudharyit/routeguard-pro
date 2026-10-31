# Verification and acceptance

## Automated checks (developer-reported, October 31, 2026)

| Check | Result |
| --- | --- |
| `python manage.py check` | No issues |
| `python manage.py test` | 25 passed |
| `npm test` | 4 passed |
| `npm run build` | TypeScript and Vite build passed |
| `npm ci --include=dev` | Audit reported 0 vulnerabilities |

These results were provided from the developer's Mac. They do not establish successful production deployment or independent live-provider testing.

## Manual acceptance checklist

- [ ] Analyze Dallas, TX → Atlanta, GA with a future departure.
- [ ] Switch route alternatives; verify geometry, map markers and checkpoint data update together.
- [ ] Review arrival-time risk and distinguish it from fixed-hour +0h to +48h weather corridor forecasts.
- [ ] Open checkpoint details; locate the checkpoint on the map and reset map view.
- [ ] Test 10-, 25- and 50-mile checkpoint spacing.
- [ ] Stop the backend; verify error messaging, preserved previous results and Retry Analysis after restart.
- [ ] Check responsive layout, dialog focus/close behavior and map controls at mobile widths.
- [ ] Verify unavailable forecasts are not presented as safe.
- [ ] Verify browser network requests target the correct API host.

## Known limitations

Public provider data may be unavailable or rate-limited; routing is not truck-restriction aware; weather risk is advisory, not a safety guarantee. No production-hosted end-to-end run is claimed.
