# Custom-Domain Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

> **Status:** Tentative. This records the agreed target state and the currently known migration sequence. Each live DNS, hosting, or paid-service change still requires Riley's confirmation at the point of action.

**Goal:** Make `rileymurray.ai` the canonical GitHub Pages address, permanently redirect `rileyjmurray.com` and `www.rileyjmurray.com` to it, and remove the visible WordPress.com site from the public path.

**Architecture:** Cloudflare manages DNS for both domains. GitHub Pages serves the Jekyll site under `rileymurray.ai`; Cloudflare handles the permanent `.com` redirect. WordPress.com remains only the registrar for `.com` and, until a separate paid Site Redirect is configured, the host for `rileyjmurray.wordpress.com`.

**Tech Stack:** Jekyll, GitHub Pages, Cloudflare DNS and Redirect Rules, Namecheap, WordPress.com domain management.

**Spec:** `docs/superpowers/plans/2026-08-30-custom-domain-migration.md` (this tentative migration plan).

## Global Constraints

- Canonical public URL: `https://rileymurray.ai`.
- Preserve the request path and query string on all permanent `.com` redirects.
- Keep the four GitHub Pages apex A records and the `www` CNAME in the `.ai` zone. They are temporarily proxied only while the Cloudflare bridge redirect is active; return them to DNS-only before serving GitHub Pages directly.
- Riley accepts the residual risk that an untested recursive resolver could still cache the removed `.com` DNSSEC DS records; do not delay the `.com` nameserver change solely for the former 24–48-hour buffer.
- Do not detach either custom domain from WordPress.com until the new routing has been verified.
- Do not purchase WordPress.com Site Redirect without an explicit approval at checkout.
- After each live change, verify DNS answers and HTTP behavior before advancing.

---

## Current State

- [x] Created a Cloudflare zone for `rileymurray.ai`.
- [x] Replaced the imported WordPress DNS records in that zone with these DNS-only GitHub Pages records:

  ```text
  A      @      185.199.108.153
  A      @      185.199.109.153
  A      @      185.199.110.153
  A      @      185.199.111.153
  CNAME  www    rileyjmurray.github.io
  ```

- [x] Changed `rileymurray.ai` at Namecheap from the three WordPress.com nameservers to:

  ```text
  josh.ns.cloudflare.com
  wally.ns.cloudflare.com
  ```

- [x] Created a Cloudflare zone for `rileyjmurray.com`; it contains four GitHub Pages A records and one `www` CNAME imported from the current live DNS.
- [x] Disabled DNSSEC for `rileyjmurray.com` in WordPress.com. The `.com` registry no longer publishes the prior DS records.
- [x] Confirmed Cloudflare reports the `rileymurray.ai` zone as active.
- [x] Confirmed both Cloudflare Public DNS (`1.1.1.1`) and Google Public DNS (`8.8.8.8`) delegate `rileymurray.ai` to `josh.ns.cloudflare.com` and `wally.ns.cloudflare.com`.
- [x] Confirmed both public resolvers return no DNSSEC DS records for `rileyjmurray.com`.
- [x] Riley waived the former 24–48-hour DNSSEC-cache buffer after confirming that the registry, Cloudflare Public DNS, and Google Public DNS have cleared the old DS records.
- [x] Proxied the four `.ai` apex A records and its `www` CNAME while the temporary Cloudflare bridge is active.
- [x] Deployed an enabled temporary Cloudflare Page Rule: `*rileymurray.ai/*` → `https://rileyjmurray.com/$2` with status **302 Temporary Redirect**.
- [x] Verified both `rileymurray.ai` and `www.rileymurray.ai` return that 302 while preserving `/temporary-bridge-test?bridge=check`.
- [x] Added GitHub's `_github-pages-challenge-rileyjmurray` TXT record to the active `.ai` Cloudflare zone and verified it from Cloudflare Public DNS.
- [x] Verified `rileymurray.ai` as a GitHub Pages protected domain.
- [x] Set `rileymurray.ai` as the GitHub Pages custom domain; GitHub reports its DNS check is in progress and HTTPS is not yet available.

## Files Affected at Cutover

- Modify: `CNAME:1` — change `rileyjmurray.com` to `rileymurray.ai`.
- Modify: `_config.yml:22` — change the Jekyll `url` from `https://rileyjmurray.com` to `https://rileymurray.ai`.
- Create: `docs/superpowers/plans/2026-08-30-custom-domain-migration.md` — this migration checklist.

## Task 1: Validate the Two Waiting Conditions

**External systems:** Cloudflare, public DNS, WordPress.com.

- [x] Confirm Cloudflare reports the `rileymurray.ai` zone as **Active**.
- [x] Confirm public DNS delegates `rileymurray.ai` to `josh.ns.cloudflare.com` and `wally.ns.cloudflare.com`.
- [x] Confirm the Cloudflare public resolver returns all four GitHub Pages A addresses for `rileymurray.ai` and `rileyjmurray.github.io` as the CNAME target for `www.rileymurray.ai`.
- [x] Confirm `dig DS rileyjmurray.com` returns no DS records from the Cloudflare and Google public recursive resolvers before the `.com` nameserver change.
- [x] Record Riley's explicit decision to proceed without the former 24–48-hour DNSSEC-cache buffer. The residual risk is a temporary `SERVFAIL` for visitors using a resolver that still has the removed DS records cached.

## Task 2: Use a Temporary `.ai` Bridge Before the GitHub Pages Cutover

**External systems:** Active Cloudflare `.ai` zone.

**Decision gate:** This step needs an explicit approval because it temporarily changes live `.ai` traffic. Riley approved it on 2026-08-30.

- [x] Add a temporary Cloudflare redirect rule that sends requests for both `rileymurray.ai` and `www.rileymurray.ai` to the existing working site at `https://rileyjmurray.com`.
- [x] Preserve the request path and query string in that temporary redirect.
- [x] Use the temporary rule only after the `.ai` zone becomes active and before GitHub Pages is switched to the `.ai` custom domain.
- [ ] Remove the temporary rule as soon as `https://rileymurray.ai` successfully serves the GitHub Pages site. Leaving it in place after the final `.com` redirect would create a redirect loop.

## Task 3: Prepare GitHub Pages and the Site Configuration

**Files:**

- Modify: `CNAME:1`.
- Modify: `_config.yml:22`.

**External systems:** GitHub account settings, Cloudflare DNS.

- [x] Add and verify `rileymurray.ai` as a GitHub Pages verified domain using the exact TXT record GitHub supplies. Add the TXT record to the active Cloudflare `.ai` zone.
- [ ] Confirm the temporary `.ai → .com` bridge from Task 2 is live before replacing the GitHub Pages custom domain.
- [x] Confirm the temporary `.ai → .com` bridge from Task 2 is live before replacing the GitHub Pages custom domain.
- [x] In GitHub repository settings for `rileyjmurray/rileyjmurray.github.io`, replace the Pages custom domain `rileyjmurray.com` with `rileymurray.ai`.
- [x] Change `CNAME` to the single line below so future Jekyll deployments retain the new domain:

  ```text
  rileymurray.ai
  ```

- [x] Change the Jekyll setting to the exact value below:

  ```yaml
  url: https://rileymurray.ai
  ```

- [ ] Deploy the configuration change through the existing GitHub Pages workflow and wait for GitHub Pages to recognize the new domain.
- [ ] Remove the temporary bridge only after a direct request to `https://rileymurray.ai` serves the new GitHub Pages site without a redirect to `.com`.
- [ ] Enable **Enforce HTTPS** in GitHub Pages only after GitHub has issued a valid certificate for `rileymurray.ai`.

## Task 4: Activate the `.com` Redirect

**External systems:** Cloudflare `.com` zone, WordPress.com domain management.

**Decision gate:** This task changes the live routing for `rileyjmurray.com` and requires an explicit confirmation immediately before the nameserver save.

- [ ] Confirm Tasks 1 through 3 are complete: public checks remain clear of the old DS records, `rileymurray.ai` is healthy on GitHub Pages, and HTTPS is ready or pending issuance.
- [ ] In the staged Cloudflare `.com` zone, create a permanent 301 redirect rule matching both `rileyjmurray.com` and `www.rileyjmurray.com`.
- [ ] Set the redirect destination to `https://rileymurray.ai` while preserving the incoming path and query string.
- [ ] Continue the Cloudflare `.com` activation flow and record the two assigned Cloudflare nameservers.
- [ ] In WordPress.com for `rileyjmurray.com`, turn off **Use WordPress.com name servers**, enter the two assigned Cloudflare nameservers, and save.
- [ ] Leave the domain registered at WordPress.com and attached to the site until the redirect has been verified. Do not use the domain deletion control.
- [ ] Verify the Cloudflare zone becomes active and that both `.com` hostnames return a 301 to the equivalent `.ai` URL.

> Note: During the `.com` nameserver change, some recursive resolvers may continue using the old WordPress.com nameservers until their NS cache expires. A short convergence period is expected.

## Task 5: Remove the WordPress.com Public Entry Point

**External systems:** WordPress.com Site Redirect.

**Decision gate:** WordPress.com Site Redirect is a paid service. Confirm its price and obtain explicit approval before checkout.

- [ ] Purchase and configure WordPress.com Site Redirect for `rileyjmurray.wordpress.com` with destination `https://rileymurray.ai`.
- [ ] Confirm a request to `https://rileyjmurray.wordpress.com` receives a permanent redirect to the canonical `.ai` domain.
- [ ] After all custom-domain redirects work, optionally detach `rileyjmurray.com` and `rileymurray.ai` from the old WordPress.com site. Detaching is dashboard cleanup only; it must not be used as a substitute for the redirect checks above.

## Task 6: Restore DNSSEC and Verify the Completed Migration

**External systems:** Cloudflare, Namecheap, WordPress.com, GitHub Pages, public DNS.

- [ ] Enable DNSSEC in the active Cloudflare `.ai` zone and copy Cloudflare's generated DS record to Namecheap.
- [ ] Enable DNSSEC in the active Cloudflare `.com` zone and copy Cloudflare's generated DS record to WordPress.com.
- [ ] Verify DNSSEC validation succeeds for both domains after the new DS records propagate.
- [ ] Verify all final URL behaviors:

  | Source URL | Expected result |
  | --- | --- |
  | `https://rileymurray.ai` | GitHub Pages site over HTTPS |
  | `https://www.rileymurray.ai` | Redirect to `https://rileymurray.ai` |
  | `https://rileyjmurray.com/path?x=1` | 301 to `https://rileymurray.ai/path?x=1` |
  | `https://www.rileyjmurray.com/path?x=1` | 301 to `https://rileymurray.ai/path?x=1` |
  | `https://rileyjmurray.github.io` | Redirect to `https://rileymurray.ai` |
  | `https://rileyjmurray.wordpress.com` | Permanent redirect to `https://rileymurray.ai` |

## Sources

- [Cloudflare DNSSEC migration guidance](https://developers.cloudflare.com/dns/dnssec/)
- [WordPress.com name-server instructions](https://wordpress.com/support/domains/change-name-servers/)
- [WordPress.com DNSSEC instructions](https://wordpress.com/support/domains/dnssec-on-wordpress-com/)
- [GitHub Pages custom-domain troubleshooting](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/troubleshooting-custom-domains-and-github-pages)
