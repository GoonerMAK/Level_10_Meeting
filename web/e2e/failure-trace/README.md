# Failure trace

A run with one expectation deliberately broken: after the facilitator clicks Next: IDS, the test expected the second browser's heading to read "Identify" instead of "IDS". The change was reverted straight after.

- `trace.zip`: both browsers' actions, network, console and DOM snapshots up to the failure.
- `second-browser.png`: the second browser at the failure. It had followed to IDS, so the app was right and the expectation was wrong.

Open it with `pnpm --dir web exec playwright show-trace e2e/failure-trace/trace.zip`, or drop the file on trace.playwright.dev.
