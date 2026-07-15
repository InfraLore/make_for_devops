# Chapter 16: Make for Logging and Incident Response

\chaptersubtitle{Transforming chaos into discoverable, executable runbooks that capture team expertise and accelerate incident resolution.}

The post-mortem document tells a familiar story: "At 14:37 UTC, users began experiencing login failures. The on-call engineer investigated logs but initially checked the wrong service. After 15 minutes, they realized the authentication service was failing. They found the relevant logs, identified a database connection issue, but struggled to locate the correct restart procedure. A senior engineer was pulled into the incident. Total time to resolution: 47 minutes."

The post-mortem asks: "Why did it take 15 minutes to find the right logs? Why didn't the on-call engineer know the restart procedure?" The uncomfortable answer: the knowledge existed, but wasn't discoverable when needed.

When services are failing and users are impacted, engineers don't read documentation. They need to **act**. They need commands to run, not procedures to follow. They need discovery, not search.

Make offers a solution: **encode your incident response procedures as executable runbooks**. Instead of documentation that describes what to do, create targets that do it directly, with built-in context and validation.

## The Hidden Cost of Undocumented Incident Response

Traditional incident response relies on human memory and experience. Senior engineers build up mental models of where logs live, what patterns indicate specific problems, which fixes work for which symptoms. This knowledge becomes team lore: passed down through observation, accumulated through painful experience, and lost when people change roles.

The costs:

**Slow Resolution**: Junior engineers spend precious minutes trying to find the right commands or remember diagnostic steps.

**Inconsistent Response**: Different engineers approach the same problem differently, making it harder to identify patterns.

**Knowledge Concentration**: Critical response knowledge concentrates in a few senior engineers who become bottlenecks.

**Training Friction**: New team members can't practice incident response safely.

**Lost Lessons**: Hard-won insights from past incidents fade from memory.

Make-based incident runbooks address these by making incident response procedures discoverable, executable, and improvable.

## Discovering Incident Response

Here's the traditional documentation approach:

```markdown
# Database Connection Pool Exhaustion Response

## Symptoms
- API response times spike above 2s
- Database connection errors in logs
- Connection pool metrics show 100% utilization

## Diagnosis Steps
1. Check API response times: kubectl logs...
2. Check connection pool: kubectl exec...
3. Check for long-running queries: psql...

## Resolution
1. If long-running queries found, kill them
2. Restart API pods to reset connection pool
3. Monitor recovery
```

This requires you to remember complex commands, doesn't validate context, and doesn't protect you from dangerous operations.

Here's the discovery-based approach:\footnote{Script delegation pattern---see Chapter 21 for how this aids learning.}

```makefile
.PHONY: incident-help incident-db-pool

incident-help: ## Show incident response runbooks
	@echo "Incident Response Runbooks"
	@echo "=========================="
	@echo "  incident-db-pool      - Database connection issues"
	@echo "  incident-api-latency  - High API latency"
	@echo "  incident-cache-down   - Cache failures"
	@echo ""
	@echo "Start with health check: make health-check"

incident-db-pool: ## Diagnose database connection pool issues
	@echo "Diagnosing database connection pool..."
	@./scripts/check-api-latency.sh 
	@./scripts/check-connection-pool.sh
	@./scripts/check-long-queries.sh
	@echo ""
	@echo "Next steps:"
	@echo "  make incident-db-restart    - Restart API pods"
	@echo "  make incident-db-kill       - Kill long queries"

incident-db-restart: ## Restart API to reset connection pool
	@echo "About to restart API pods in production"
	@echo -n "Continue? [y/N] " && read ans && [ $${ans:-N} = y ]
	@./scripts/restart-api-pods.sh
	@echo "Monitor with: make incident-watch-recovery"
```

When that 2 AM alert comes in, you run `make incident-help`, see `incident-db-pool`, and follow the guided procedure. The workflow reveals itself progressively.

## Building Discoverable Runbook Systems

A complete incident response system has layers that reveal themselves as needed:

### Discovery Layer: Quick Triage

```makefile
health-check: ## Quick system health check
	@echo "System Health Check"
	@echo "==================="
	@$(MAKE) -s _check-api && echo "API" || echo "API"
	@$(MAKE) -s _check-db && echo "Database" || echo "Database"
	@$(MAKE) -s _check-cache && echo "Cache" || echo "Cache"
	@echo ""
	@echo "For diagnosis: make incident-help"

_check-api:
	@./scripts/check-api-health.sh >/dev/null

_check-db:
	@./scripts/check-db-health.sh >/dev/null
```

### Scenario Layer: Common Problems

```makefile
incident-api-latency: ## Diagnose API latency issues
	@echo "Investigating API Latency"
	@echo "========================="
	@echo "Current latency:"
	@./scripts/query-latency.sh
	@echo ""
	@echo "Checking common causes..."
	@./scripts/check-slow-queries.sh
	@./scripts/check-cache-hit-rate.sh
	@./scripts/check-api-resources.sh
	@echo ""
	@echo "Suggested actions:"
	@./scripts/suggest-latency-fixes.sh
```

### Action Layer: Guided Resolution

```makefile
incident-scale-api: ## Scale up API capacity
	@echo "Scaling API replicas..."
	@./scripts/scale-api.sh
	@echo "Monitor: make incident-watch-scaling"

incident-cache-warm: ## Warm cache with common queries
	@echo "Warming cache..."
	@./scripts/warm-cache.sh

incident-maintenance-mode: ## Enable maintenance mode
	@echo "ENABLING MAINTENANCE MODE"
	@echo -n "Continue? [y/N] " && read ans && [ $${ans:-N} = y ]
	@./scripts/enable-maintenance.sh
	@echo "To disable: make incident-normal-mode"
```

Notice the pattern: each layer provides just enough information and points to the next step. The complexity is hidden in scripts, but the workflow is discoverable.

## Discovering Through Logs

Effective incident response requires quick access to relevant logs:

```makefile
logs: ## Show log access commands
	@echo "Log Access Commands"
	@echo "==================="
	@echo "  make logs-api         - Recent API logs"
	@echo "  make logs-errors      - Error logs"
	@echo "  make logs-search Q=.. - Search logs"
	@echo "  make logs-tail        - Live log stream"

logs-api: ## Show recent API logs
	@echo "API logs (last 10 min):"
	@./scripts/fetch-api-logs.sh

logs-errors: ## Show error logs with context
	@echo "Error logs (last 1 hour):"
	@./scripts/fetch-error-logs.sh
	@echo ""
	@echo "For context: make logs-error-details"

logs-search: ## Search logs (make logs-search Q="term")
	@test -n "$(Q)" || (echo "Usage: make logs-search Q=\"term\"" && exit 1)
	@./scripts/search-logs.sh "$(Q)"

logs-tail: ## Tail live logs
	@echo "Live logs (Ctrl+C to stop)..."
	@./scripts/tail-logs.sh
```

Running `make logs` shows what's available. Each command provides clear, focused output and suggests next steps.

## Integrating Alerts with Runbooks

Connect your alerting system directly to runbooks:

```makefile
alert-response: ## Respond to alert (ALERT=alert_name)
	@case "$(ALERT)" in \
		"high_latency") $(MAKE) incident-api-latency ;; \
		"db_connections") $(MAKE) incident-db-pool ;; \
		"high_errors") $(MAKE) incident-api-errors ;; \
		*) echo "Unknown alert. Try: make incident-help" ;; \
	esac
```

Your PagerDuty alerts can include:

```
Alert: High API Latency
Runbook: make incident-api-latency
```

The alert tells you exactly what to run. No searching, no guessing.

## Capturing Team Expertise

When a senior engineer resolves a novel incident, the procedure becomes a new target:

```makefile
incident-queue-backlog: ## Diagnose message queue backlog
	@echo "Checking message queue..."
	@./scripts/check-queue-depth.sh
	@./scripts/check-worker-status.sh
	@./scripts/check-worker-errors.sh
	@echo ""
	@echo "Common fix: make incident-restart-workers"

incident-restart-workers: ## Restart worker processes
	@echo "Restarting workers..."
	@./scripts/restart-workers.sh
	@echo "Monitor: make watch-queue-depth"
```

That expertise is now available to everyone, including the engineer who created it when they're on-call six months later.

## Safe Practice Environments

Enable safe practice of incident response:

```makefile
incident-practice: ## Practice incident response (staging only)
	@test "$(ENV)" = "staging" \
	|| (echo "Practice only in staging!" && exit 1)
	@echo "Incident Response Practice"
	@echo "=========================="
	@echo "Available scenarios:"
	@echo "  1. make practice-latency"
	@echo "  2. make practice-db-pool"
	@echo "  3. make practice-cache-down"

practice-latency: ## Practice latency incident
	@echo "Starting latency scenario..."
	@./scripts/simulate-latency.sh
	@echo ""
	@echo "Diagnose: make incident-api-latency"
	@echo "Cleanup: make practice-cleanup"
```

New team members can learn without fear.

## Real-World Transformation

### Before: Incident Response via Slack

```
[2:15 AM] PagerDuty: High error rate
[2:17 AM] OnCall: How do I check error logs?
[2:23 AM] OnCall: Found logs, thousands of errors
[2:31 AM] Senior (awakened): Check cache connection
[2:33 AM] OnCall: How?
[2:35 AM] Senior: kubectl exec... curl the health endpoint
[2:40 AM] OnCall: Cache timing out. Restart?
[2:42 AM] Senior: Yeah, restart API after
[2:58 AM] OnCall: How do I restart cache in prod?
[3:15 AM] RESOLVED (MTTR: 60 minutes)
```

### After: Discovery-Based Response

```
[2:15 AM] PagerDuty: High error rate
[2:16 AM] OnCall: $ make incident-api-errors
  Analyzing errors...
  Cache connection failures (95% of errors)
  Next: make incident-cache-check
[2:17 AM] OnCall: $ make incident-cache-check
  Cache health: FAILED
  Resolution: make incident-cache-restart
[2:18 AM] OnCall: $ make incident-cache-restart
  Restarting cache...   Restarting dependent services...   Monitor: make health-check
[2:20 AM] OnCall: $ make health-check
  API  Database  Cache
[2:20 AM] RESOLVED (MTTR: 5 minutes)
```

The supporting Makefile:

```makefile
incident-api-errors: ## Diagnose high error rate
	@echo "Analyzing error patterns..."
	@./scripts/analyze-errors.sh
	@./scripts/suggest-next-step.sh

incident-cache-check: ## Check cache health
	@echo "Checking cache..."
	@./scripts/check-cache.sh \
	|| echo "Resolution: make incident-cache-restart"

incident-cache-restart: ## Restart cache and dependencies
	@echo "Restart production cache?"
	@echo -n "Continue? [y/N] " && read ans && [ $${ans:-N} = y ]
	@./scripts/restart-cache.sh
	@./scripts/restart-dependent-services.sh
	@echo "Monitor: make health-check"
```

Simple, discoverable, safe.

## Post-Incident Learning

After resolution, capture what happened:

```makefile
incident-summary: ## Generate incident summary
	@echo "Incident Summary"
	@echo "================"
	@./scripts/summarize-errors.sh
	@./scripts/summarize-timeline.sh
	@echo ""
	@echo "Save logs: make incident-save-logs"

incident-save-logs: ## Save logs for post-mortem
	@mkdir -p incidents/$(date +%Y%m%d_%H%M%S)
	@./scripts/save-incident-logs.sh
	@echo "Logs saved for analysis"
```

The runbook helps with both resolution and learning.

## Key Takeaways

Make-based incident response transforms how teams handle production issues:

1. **Discoverability**: Find and execute response procedures without prior knowledge
2. **Consistency**: Everyone follows the same diagnostic and resolution steps
3. **Speed**: No time wasted searching for commands
4. **Safety**: Built-in validation and confirmation for destructive operations
5. **Learning**: Runbooks teach the system while solving problems
6. **Evolution**: Easy to update based on new insights

The goal isn't to automate away judgment—incidents often require creative problem-solving. Instead, runbooks handle routine parts (finding logs, checking health, executing common fixes) so engineers can focus on novel aspects.

Most importantly, these runbooks capture team knowledge in executable form. That 2 AM incident response expertise that used to live only in senior engineers' heads now lives in version-controlled Make targets that anyone can execute, learn from, and improve.

The pattern is consistent: start with `make incident-help` or `make logs`, discover what's available, follow the breadcrumbs. Each target provides clear output and suggests next steps. The workflow reveals itself through interaction, not through reading 23-page Google Docs at 2 AM.

In the next chapter, we'll explore how to apply similar patterns to security and compliance workflows, where discoverability and consistent execution are even more critical.
