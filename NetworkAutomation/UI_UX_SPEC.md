# NetworkAutomation — UI/UX configuration proposal

## Product direction
NetworkAutomation is a desktop NOC / network administration tool. The UI should optimize for fast scanning, safe actions, dense operational data, and predictable navigation rather than decorative visuals.

## Information architecture
Use six primary sidebar groups: Tổng quan; Thiết bị & IP; Giám sát; Tự động hóa; Sự cố & Báo cáo; Quản trị. Keep one active page highlighted. At widths below 1150 px the sidebar should collapse by default and open from the Menu button.

## Standard page anatomy
1. Page header: title, one-line purpose/status, contextual actions.
2. KPI/status summary when useful.
3. Filter/command bar.
4. Main content: table, cards, topology, form, log, or chart.
5. Details/action area with destructive actions visually separated.

## Interaction rules
- One primary CTA per local context.
- Destructive actions use danger styling and require confirmation when data/state changes are irreversible.
- Long network actions always show state: idle → running → success / warning / failure / cancelled.
- Preserve filter/search values while opening details and returning to the list.
- Double-click table row opens details; right-click may expose contextual actions, but all critical actions must also be available visibly.
- Empty states explain what data is missing and the next useful action.
- Never use color alone to communicate health; pair color with text/icon/status value.

## Responsive rules
- 1400×800: full sidebar, 3–4 KPI cards, two-column forms.
- 1024–1399: full or collapsible sidebar, 2–3 KPI cards, two-column forms where space allows.
- 800×600: sidebar hidden by default, one-column forms, horizontal table scroll, actions wrap to multiple rows.

## Visual system
Central tokens live in `modules/ui_ux_config.py`. Existing pages continue to access `modules.ui_theme.PALETTE`, so migration can be gradual. Use Segoe UI, a dark blue-black background, cyan for primary focus/action, and semantic success/warning/danger/info colors.

## Highest-priority screens to redesign first
1. Tổng quan / Trung tâm NOC — decision dashboard, health and incident priority.
2. Quản lý thiết bị — search/filter/table/action consistency.
3. Khám phá mạng — progress, live state, cancellation, result triage.
4. Cảnh báo / Trung tâm sự cố — severity, acknowledgement, assignment, timeline.
5. SSH / Automation — credential context, run state, output readability and safety.

## Migration sequence
Phase 1: tokens + navigation + page header + buttons/table styles.
Phase 2: standard list/form/monitor page templates.
Phase 3: redesign five priority workflows above.
Phase 4: accessibility, DPI 125–150%, keyboard navigation and Windows 11 visual QA.
