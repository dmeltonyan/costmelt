# CLAUDE.md

This repository is a full-stack LLM cost optimization platform called Cost Melt. The product is meant to sit in front of LLM providers and reduce cost automatically through model routing, semantic caching, prompt compression, and request batching.

## What this project is

Cost Melt is not just a demo app. It is meant to behave like a production-grade LLM gateway:

- A backend service receives prompts and decides how to process them efficiently.
- It can route requests to cheaper or more suitable models.
- It can reuse prior responses for similar prompts.
- It can reduce prompt size before sending work to providers.
- It can batch compatible requests to reduce overhead.
- It can record usage, costs, and savings for analytics.

The repo has three main areas:

1. Backend
   - Python/FastAPI service
   - Core request orchestration
   - Routing, caching, compression, queueing, cost tracking

2. Dashboard
   - Next.js app for usage insights and metrics
   - Charts, summaries, and operational views

3. Landing page
   - Marketing site for product positioning and conversion

## What is already in place

The repository already has a solid foundation:

- A real FastAPI backend entry point
- A central gateway route for orchestration
- Separate modules for routing, caching, compression, and batching
- A dashboard with charts and stats pages
- Docker-based infrastructure for local development
- A documented product direction and architecture

That means the repo is not a blank slate. It already has the bones of a serious product.

## What is missing or weak

The biggest issue is not missing ideas. The biggest issue is maturity and production readiness. The repo currently feels more like an ambitious prototype than a fully hardened product.

### Main gaps

1. Security is still too loose
   - CORS is open to all origins
   - Authentication and authorization are not fully implemented
   - API key handling is still underdeveloped

2. The system has too many placeholders
   - Some modules contain placeholder logic rather than complete behavior
   - Some pieces are wired structurally but not fully production-ready

3. Reliability is not yet strong enough
   - Error handling should be more consistent
   - Queue and provider interactions should be more resilient
   - Failure states need clearer behavior and better logging

4. The dashboard is only partially complete
   - Some pages are still stubbed or incomplete
   - Data flows should be connected more cleanly to real backend logic

5. Testing and operational confidence are still weak
   - The repo should have stronger integration tests and clearer verification steps
   - CI, health checks, and observability should be improved

## Senior-level assessment

If this were being built for real customers, the next step is not “add more features.” The next step is to harden the foundation.

The work should focus on four things in order:

1. Make the product safe and trustworthy
2. Make the core request path reliable
3. Make the dashboard useful and connected to real data
4. Make deployment and operations predictable

## Development principles for this repo

Follow these rules while working here:

- Prefer reliability over novelty.
- Make the backend predictable before adding more product features.
- Keep configuration external and explicit.
- Do not leave placeholder logic in core paths.
- Build tests around real behavior, not mock-only behavior.
- Make every change measurable and verifiable.
- Keep the architecture understandable. This repo is already broad; avoid unnecessary complexity.

## Recommended development order

### Phase 1: Stabilize the foundation

Start with the basics that affect everything else.

1. Make configuration clean and explicit
   - Ensure environment variables are clearly defined
   - Avoid hidden defaults that make debugging hard
   - Document required variables for backend, dashboard, and database

2. Make the backend safer
   - Lock down CORS and request handling
   - Add proper authentication and request validation
   - Ensure failures return structured, useful errors

3. Replace obvious placeholders
   - Review modules with TODOs and incomplete logic
   - Convert placeholder behavior into real, tested implementations where possible

### Phase 2: Make the core request pipeline dependable

The main value of this product is the request path. That path should be robust.

1. Improve the gateway flow
   - Ensure requests go through the pipeline predictably
   - Make each stage observable and debuggable
   - Handle partial failures without breaking the whole request path

2. Improve routing behavior
   - Ensure routing decisions are explainable
   - Add fallback behavior for provider or model failures
   - Make model selection deterministic and auditable

3. Improve caching behavior
   - Make cache lookup and storage behavior consistent
   - Log hit rate and relevant metadata clearly
   - Ensure cache failures degrade gracefully

4. Improve provider integration
   - Handle network errors and provider-specific failures properly
   - Add retries and timeouts where appropriate
   - Avoid silently failing when a provider call breaks

### Phase 3: Make the data layer useful

The product is stronger when logs, metrics, and savings data are trustworthy.

1. Make logging consistent
   - Store request metadata in a reliable way
   - Ensure cost and token totals are calculated correctly
   - Record enough detail for debugging and finance tracking

2. Make dashboard data real and trustworthy
   - Connect charts to real backend data instead of placeholder or weak flows
   - Make empty states and error states clear
   - Ensure the dashboard reflects the same data model as the backend

3. Improve analytics quality
   - Show true savings, not just optimistic estimates
   - Make routing and cache metrics easier to understand
   - Add clear definitions for each metric

### Phase 4: Make the product production-ready

Once the core is stable, focus on operational maturity.

1. Add stronger observability
   - Structured logs
   - Request tracing
   - Health and readiness endpoints
   - Better error reporting

2. Add better testing
   - Integration tests for the gateway path
   - Tests for routing logic and cache behavior
   - Frontend tests for core dashboard flows

3. Improve deployment and release safety
   - Make local startup reliable
   - Ensure Docker and environment setup are straightforward
   - Add a basic CI path for linting and tests

## Concrete priorities for the next implementation cycle

If you want to make meaningful progress quickly, focus on these in order:

1. Authentication and authorization
   - Add real identity and access control
   - Protect internal endpoints and admin functionality

2. Environment and config hardening
   - Replace loose defaults with explicit settings
   - Fail fast when required services are not configured

3. Backend error handling and observability
   - Add consistent error contracts
   - Improve logs for debugging and support

4. Dashboard completion
   - Finish the incomplete pages and connect to real data

5. Test coverage and regression safety
   - Add a small but high-value test suite around the core request path

## Suggested implementation style

Work in small, verifiable steps.

For each feature or fix:

1. Understand the current behavior
2. Add or update a test that captures the expected behavior
3. Implement the smallest change that solves the problem
4. Verify the change through testing or a real run
5. Document the result if it affects onboarding or operations

Do not try to redesign the whole system at once. The repo already has structure; the goal is to strengthen it incrementally.

## Plain-English guidance for future work

When you work in this repository, think of it like this:

- The backend is the core product.
- The dashboard is the visibility layer.
- The landing page is the sales layer.
- The biggest value comes from making the backend efficient and trustworthy.

So the most important question is not “How do we add another UI feature?” It is:

- Does the request pipeline work reliably?
- Does the system behave safely under failure?
- Can a user trust the savings and routing decisions?
- Can a developer understand and extend the system quickly?

## Definition of done for meaningful progress

A change should be considered successful if:

- It improves reliability or clarity
- It is covered by a test or a clear verification step
- It does not introduce hidden configuration risk
- It fits the existing architecture without unnecessary complexity

## Recommended first milestone

The best first milestone is this:

- Make the backend request flow work end-to-end with clear validation
- Add authentication protection around sensitive routes
- Make the dashboard show trustworthy, real data
- Ensure the repo can be started locally without confusing setup gaps

That milestone will make the project feel much more like a real product and much less like a collection of promising modules.
