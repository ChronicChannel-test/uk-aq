# UK AQ Feature TODO

## Goal
Add user features so people can:
- create/login to an account
- save favourite sensors
- optionally receive email alerts

## Auth Options

### Option 1: Supabase passwordless magic link (Recommended)
Pros:
- fastest to ship
- lower password/security burden
- good UX for occasional users
Cons:
- depends on email delivery reliability
- some users prefer password login

### Option 2: Supabase email + password
Pros:
- familiar login flow
- works even if magic-link email is delayed
Cons:
- more UX and security overhead (reset flows, password policies)

## TODO

### Phase 1: Accounts
- [ ] Confirm auth method (magic link vs password)
- [ ] Add auth UI (sign up, sign in, sign out)
- [ ] Add protected user menu state in frontend
- [ ] Add basic profile table (display name, created_at, last_login_at)

### Phase 2: Favourite Sensors
- [ ] Create `user_favourite_sensors` table (`user_id`, `sensor_id`, `created_at`)
- [ ] Add unique constraint on (`user_id`, `sensor_id`)
- [ ] Add RLS policies so users can only read/write their own favourites
- [ ] Add "Save/Unsave sensor" action in map/chart UI
- [ ] Add "My favourites" list view

### Phase 3: Email Alerts (Optional / Maybe)
- [ ] Define alert types:
- [ ] `threshold_crossed` (PM2.5 above user threshold)
- [ ] `daily_summary` (single digest of favourite sensors)
- [ ] Create `user_alert_preferences` table
- [ ] Add backend job/edge function to evaluate alerts on schedule
- [ ] Add email provider integration (e.g., Resend/Postmark)
- [ ] Add alert settings UI (on/off, threshold, frequency)

### Phase 4: Quality + Safety
- [ ] Add telemetry for auth errors and failed alert sends
- [ ] Add tests for favourites CRUD and RLS rules
- [ ] Add unsubscribe link and consent text for alerts
- [ ] Add rate limits/debounce for notification spam prevention

## Suggested First Slice
Ship in this order:
1. Magic-link login
2. Save favourite sensors
3. Basic daily email summary (then threshold alerts later)
