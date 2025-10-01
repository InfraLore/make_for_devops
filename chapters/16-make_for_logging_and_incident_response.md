# Chapter 16 - Make for Logging and Incident Response

\chaptersubtitle{Transforming chaos into discoverable, executable runbooks that capture team expertise and accelerate incident resolution.}

The post-mortem document tells a familiar story: "At 14:37 UTC, users began experiencing login failures. The on-call engineer investigated logs but initially checked the wrong service. After 15 minutes, they realized the authentication service was failing. They found the relevant logs, identified a database connection issue, but struggled to locate the correct restart procedure. A senior engineer was pulled into the incident. Total time to resolution: 47 minutes. Impact: 12,000 failed login attempts."

The post-mortem asks: "Why did it take 15 minutes to find the right logs? Why didn't the on-call engineer know the restart procedure?" The uncomfortable answer appears in every blameless post-mortem: the knowledge existed, but wasn't discoverable when needed.

Your team has detailed runbooks. There's a comprehensive Google Doc titled "Authentication Service Incident Response" with 23 pages covering every scenario. There's a Confluence space with troubleshooting guides. There's a Slack channel where people ask "how do I check the auth logs again?" The problem isn't lack of documentation—it's that **documentation doesn't work during incidents**.

When services are failing and users are impacted, engineers don't read documentation. They need to **act**. They need commands to run, not procedures to follow. They need discovery, not search. They need validation, not hope.

Make offers a radical solution: **encode your incident response procedures as executable runbooks**. Instead of documentation that describes what to do, create targets that do it directly, with built-in context and validation.

## The Hidden Cost of Undocumented Incident Response

Traditional incident response relies heavily on human memory and experience. Senior engineers build up a mental model of the system—where logs live, what patterns indicate specific problems, which fixes work for which symptoms. This knowledge becomes team lore: passed down through observation, accumulated through painful experience, and lost when people change roles or leave the company.

The costs of this approach are substantial:

**Slow Time to Resolution**: Junior engineers spend precious minutes during incidents trying to find the right commands, locate the right logs, or remember the sequence of diagnostic steps.

**Inconsistent Response**: Different engineers approach the same problem differently, making it harder to identify patterns or measure improvement.

**Knowledge Concentration**: Critical response knowledge becomes concentrated in a few senior engineers who become bottlenecks (and who burn out from being the only ones who "really understand" the system).

**Training Friction**: New team members can't practice incident response because there's no clear place to start or safe way to learn.

**Lost Lessons**: Hard-won insights from past incidents fade from memory without a structured way to capture them.

Make-based incident runbooks address all of these problems by making incident response procedures discoverable, executable, and improvable.

## Incident Response as Executable Documentation

Let's start with a realistic example. Imagine you support an e-commerce platform that occasionally experiences database connection pool exhaustion. Here's how traditional documentation might capture the response procedure:

```markdown
# Database Connection Pool Exhaustion Response

## Symptoms
- API response times spike above 2s
- Database connection errors in logs
- Connection pool metrics show 100% utilization

## Diagnosis Steps
1. Check API response times: `kubectl logs -n production deploy/api | grep "request_time"`
2. Check connection pool: `kubectl exec -n production deploy/api -- curl localhost:8080/metrics | grep pool`
3. Check for long-running queries: `psql -h db.prod.company.com -U admin -c "SELECT * FROM pg_stat_activity WHERE state = 'active' AND query_start < now() - interval '30 seconds'"`

## Resolution
1. If long-running queries found, identify and kill them
2. Restart API pods to reset connection pool: `kubectl rollout restart -n production deploy/api`
3. Monitor recovery
```

This documentation has several problems. It requires you to remember (or look up) complex commands. It doesn't validate that you're in the right context. It doesn't protect you from dangerous operations. And it doesn't capture the nuance of when to do what.

Here's the same response procedure as Make targets:

```makefile
# Incident Response Runbook - Database Issues
.PHONY: incident-help incident-db-pool incident-db-slow

incident-help: ## Show incident response commands
	@echo "Incident Response Runbooks"
	@echo "=========================="
	@awk '/^incident-[a-zA-Z_-]+:.*##/ { \
		printf "  \033[31m%-25s\033[0m %s\n", $$1, substr($$0, index($$0, "##")+2) \
	}' $(MAKEFILE_LIST)

incident-db-pool: ## Diagnose database connection pool issues
	@echo "🔍 Diagnosing database connection pool..."
	@echo ""
	@echo "1️⃣ Checking API response times (last 5 min)..."
	@kubectl logs -n production deploy/api --since=5m | \
		grep "request_time" | awk '{print $$4}' | \
		awk '{sum+=$$1; count++} END {if(count>0) print "Avg:", sum/count, "ms"}'
	@echo ""
	@echo "2️⃣ Checking connection pool status..."
	@kubectl exec -n production deploy/api-0 -- \
		curl -s localhost:8080/metrics | grep "pool_active"
	@echo ""
	@echo "3️⃣ Checking for long-running queries..."
	@echo "   (Queries running >30s)"
	@$(MAKE) _check-long-queries
	@echo ""
	@echo "💡 Next steps:"
	@echo "   - If pool is exhausted: make incident-db-pool-restart"
	@echo "   - If long queries found: make incident-db-kill-queries"
	@echo "   - If issue persists: make incident-db-scale"

incident-db-pool-restart: ## Restart API to reset connection pool
	@echo "⚠️  About to restart API pods in production"
	@echo "This will cause brief downtime during pod startup."
	@echo -n "Continue? [y/N] " && read ans && [ $${ans:-N} = y ]
	@echo "Restarting API deployment..."
	kubectl rollout restart -n production deploy/api
	@echo "Waiting for rollout to complete..."
	kubectl rollout status -n production deploy/api
	@echo "✅ Restart complete. Monitor with: make incident-db-monitor"

_check-long-queries:
	@psql $(DB_URL) -t -c "SELECT pid, now() - query_start as duration, \
		query FROM pg_stat_activity WHERE state = 'active' \
		AND query_start < now() - interval '30 seconds'" || \
		echo "Unable to connect to database"
```

Notice what's different:

1. **Guided Workflow**: Each target tells you what it's checking and what to do next
2. **Safety Checks**: Destructive operations require confirmation
3. **Progressive Disclosure**: Start with diagnosis, then move to resolution
4. **Contextual Help**: Commands show their output with interpretation
5. **Built-in Monitoring**: Follow-up actions are suggested automatically

When that 2 AM alert comes in, you don't need to remember anything. You run `make incident-help`, see `incident-db-pool`, and follow the guided procedure.

## Building a Comprehensive Incident Response System

A complete incident response system in Make typically includes several layers:

### Layer 1: Incident Detection and Triage

```makefile
# Quick health checks for common issues
.PHONY: health-check health-api health-db health-cache

health-check: ## Run all health checks
	@echo "🏥 System Health Check"
	@echo "===================="
	@$(MAKE) -s health-api && echo "✅ API: Healthy" || echo "❌ API: Issues"
	@$(MAKE) -s health-db && echo "✅ Database: Healthy" || echo "❌ DB: Issues"
	@$(MAKE) -s health-cache && echo "✅ Cache: Healthy" || echo "❌ Cache: Issues"
	@echo ""
	@echo "For detailed diagnosis, run:"
	@echo "  make incident-help"

health-api:
	@curl -sf https://api.prod.company.com/health >/dev/null

health-db:
	@kubectl exec -n production deploy/api-0 -- \
		pg_isready -h db.prod.company.com >/dev/null

health-cache:
	@redis-cli -h cache.prod.company.com ping | grep -q PONG
```

### Layer 2: Common Incident Scenarios

```makefile
# Runbook for high API latency incidents
incident-api-latency: ## Diagnose API latency issues
	@echo "🐌 Investigating API Latency"
	@echo "============================"
	@echo ""
	@echo "📊 Current latency (p95, last 5 min):"
	@$(MAKE) -s _query-latency
	@echo ""
	@echo "🔍 Checking common causes:"
	@echo ""
	@echo "1. Database slow queries:"
	@$(MAKE) -s _check-slow-queries || echo "   No issues found"
	@echo ""
	@echo "2. Cache hit rate:"
	@$(MAKE) -s _check-cache-hit-rate
	@echo ""
	@echo "3. API pod resource usage:"
	@$(MAKE) -s _check-api-resources
	@echo ""
	@echo "💡 Suggested actions:"
	@$(MAKE) -s _suggest-latency-actions

_suggest-latency-actions:
	@latency=$$($(MAKE) -s _query-latency | grep -o '[0-9]\+'); \
	if [ "$$latency" -gt 2000 ]; then \
		echo "   ⚠️  Severe latency. Consider:"; \
		echo "   - make incident-api-scale (add capacity)"; \
		echo "   - make incident-enable-maintenance-mode"; \
	elif [ "$$latency" -gt 1000 ]; then \
		echo "   ⚡ Moderate latency. Try:"; \
		echo "   - make incident-cache-warm"; \
		echo "   - make incident-db-pool-restart"; \
	fi
```

### Layer 3: Resolution Actions

```makefile
# Common resolution actions with safety checks
incident-api-scale: ## Scale up API replicas
	@current=$$(kubectl get deploy -n production api \
		-o jsonpath='{.spec.replicas}'); \
	new=$$((current + 2)); \
	echo "Scaling API from $$current to $$new replicas"; \
	echo -n "Continue? [y/N] " && read ans && [ $${ans:-N} = y ]; \
	kubectl scale -n production deploy/api --replicas=$$new
	@echo "✅ Scaled to $$new replicas"
	@echo "📊 Monitor: make incident-watch-api-scaling"

incident-cache-warm: ## Warm cache with common queries
	@echo "🔥 Warming cache..."
	@./scripts/warm-cache.sh || echo "Cache warming script not found"
	@echo "✅ Cache warming initiated"

incident-enable-maintenance-mode: ## Enable maintenance mode
	@echo "⚠️  ENABLING MAINTENANCE MODE"
	@echo "This will show users a maintenance page."
	@echo -n "Continue? [y/N] " && read ans && [ $${ans:-N} = y ]
	@kubectl patch configmap -n production app-config \
		-p '{"data":{"maintenance_mode":"true"}}'
	@kubectl rollout restart -n production deploy/api
	@echo "✅ Maintenance mode enabled"
	@echo "To disable: make incident-disable-maintenance-mode"
```

### Layer 4: Post-Incident Analysis

```makefile
incident-log-summary: ## Generate incident log summary
	@echo "📝 Generating incident log summary..."
	@echo "Time range: Last 1 hour"
	@echo ""
	@echo "Error rate by endpoint:"
	@kubectl logs -n production deploy/api --since=1h | \
		grep "ERROR" | \
		awk '{print $$5}' | sort | uniq -c | sort -rn | head -10
	@echo ""
	@echo "Save this for post-mortem: make incident-save-logs"

incident-save-logs: ## Save logs for post-incident analysis
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	logdir="incidents/$$timestamp"; \
	mkdir -p $$logdir; \
	echo "Saving logs to $$logdir/..."; \
	kubectl logs -n production deploy/api --since=1h > $$logdir/api.log; \
	kubectl get events -n production > $$logdir/events.log; \
	kubectl top pods -n production > $$logdir/resources.log; \
	echo "✅ Logs saved to $$logdir/"
```

## Log Aggregation and Analysis Workflows

Effective incident response requires quick access to relevant logs. Make can provide discoverable interfaces to your logging infrastructure:

```makefile
# Log access and analysis targets
.PHONY: logs logs-api logs-errors logs-search logs-tail

logs: ## Show log access commands
	@echo "📋 Log Access Commands"
	@echo "====================="
	@echo "  make logs-api          # API logs (last 10 min)"
	@echo "  make logs-errors       # Error logs (last 1 hour)"
	@echo "  make logs-search Q=... # Search logs"
	@echo "  make logs-tail         # Tail live logs"
	@echo "  make logs-user ID=...  # Logs for specific user"

logs-api: ## Show recent API logs
	@since=$${SINCE:-10m}; \
	echo "API logs (last $$since):"; \
	kubectl logs -n production deploy/api --since=$$since | \
		grep -v "health-check" | tail -50

logs-errors: ## Show error logs with context
	@echo "🔴 Error logs (last 1 hour):"
	@kubectl logs -n production deploy/api --since=1h | \
		grep -i "error\|exception\|fatal" | \
		awk '{ printf "\033[31m%s\033[0m\n", $$0 }' | \
		tail -20
	@echo ""
	@echo "💡 For full context: make logs-error-context"

logs-search: ## Search logs (use: make logs-search Q="search term")
	@if [ -z "$(Q)" ]; then \
		echo "Usage: make logs-search Q=\"search term\""; \
		exit 1; \
	fi
	@echo "🔍 Searching for: $(Q)"
	@kubectl logs -n production deploy/api --since=1h | \
		grep -i "$(Q)" | tail -50

logs-tail: ## Tail live logs
	@echo "📡 Tailing live API logs (Ctrl+C to stop)..."
	@kubectl logs -n production deploy/api -f | \
		grep --line-buffered -v "health-check"

logs-user: ## Show logs for specific user (make logs-user ID=12345)
	@if [ -z "$(ID)" ]; then \
		echo "Usage: make logs-user ID=user_id"; \
		exit 1; \
	fi
	@echo "👤 Logs for user $(ID) (last 1 hour):"
	@kubectl logs -n production deploy/api --since=1h | \
		grep "user_id=$(ID)" | tail -30
```

## Integrating Alerts with Response Automation

One of the most powerful patterns is connecting your alerting system directly to Make-based runbooks. When an alert fires, the alert itself can suggest the relevant Make command:

```makefile
# Alert integration helpers
alert-response: ## Respond to alert (ALERT=alert_name)
	@case "$(ALERT)" in \
		"high_latency") \
			$(MAKE) incident-api-latency ;; \
		"db_connections") \
			$(MAKE) incident-db-pool ;; \
		"high_error_rate") \
			$(MAKE) incident-api-errors ;; \
		"disk_space") \
			$(MAKE) incident-disk-space ;; \
		*) \
			echo "Unknown alert: $(ALERT)"; \
			echo "Run 'make incident-help' for available runbooks" ;; \
	esac

incident-from-pagerduty: ## Import incident context from PagerDuty
	@echo "📟 PagerDuty Incident Context"
	@echo "============================"
	@if [ -z "$(INCIDENT_ID)" ]; then \
		echo "Usage: make incident-from-pagerduty INCIDENT_ID=..."; \
		exit 1; \
	fi
	@echo "Fetching incident $(INCIDENT_ID)..."
	@curl -s -H "Authorization: Token $(PAGERDUTY_TOKEN)" \
		"https://api.pagerduty.com/incidents/$(INCIDENT_ID)" | \
		jq -r '.incident | "Alert: \(.title)\nStatus: \(.status)\
		\nUrgency: \(.urgency)\nService: \(.service.summary)"'
	@echo ""
	@echo "💡 Suggested runbook:"
	@echo "   make alert-response ALERT=<alert_type>"
```

Your PagerDuty alerts can then include links like:

```
Alert: High API Latency
Runbook: make incident-api-latency
Context: make incident-from-pagerduty INCIDENT_ID=PXXX
```

## Capturing Team Expertise in Runbooks

The real power of Make-based incident response is how it captures and preserves team expertise. When a senior engineer resolves a novel incident, the procedure becomes a new Make target that everyone can use.

### Example: Evolving Runbooks

Let's say your team encounters a new issue: the message queue is backing up, causing API requests to time out. The senior engineer on call debugs it and finds that a specific worker process has crashed. Here's how that knowledge becomes institutional:

**After the incident**, the engineer adds to the Makefile:

```makefile
incident-queue-backlog: ## Diagnose message queue backlog
	@echo "📬 Checking message queue status..."
	@echo ""
	@echo "Queue depth:"
	@redis-cli -h queue.prod.company.com llen task_queue
	@echo ""
	@echo "Active workers:"
	@kubectl get pods -n production -l app=worker | grep Running | wc -l
	@echo ""
	@echo "Recent worker errors:"
	@kubectl logs -n production -l app=worker --since=10m | \
		grep ERROR | tail -5
	@echo ""
	@echo "💡 Common fix: make incident-restart-workers"

incident-restart-workers: ## Restart worker processes
	@echo "Restarting workers to clear queue backlog..."
	@kubectl rollout restart -n production deploy/worker
	@echo "✅ Workers restarting"
	@echo "Monitor queue: watch 'make _check-queue-depth'"

_check-queue-depth:
	@redis-cli -h queue.prod.company.com llen task_queue
```

Now that expertise is available to anyone, including the engineer who created it when they're bleary-eyed at 2 AM six months later.

## Safe Experimentation and Practice

One underappreciated benefit of Make-based runbooks is that they enable safe practice. New team members can learn incident response procedures without fear:

```makefile
# Staging environment incident practice
incident-practice: ## Practice incident response (staging only)
	@echo "🎓 Incident Response Practice Mode"
	@echo "=================================="
	@if [ "$(ENVIRONMENT)" != "staging" ]; then \
		echo "⚠️  Practice only works in staging!"; \
		echo "Set: ENVIRONMENT=staging"; \
		exit 1; \
	fi
	@echo ""
	@echo "Available practice scenarios:"
	@echo "  1. High latency incident"
	@echo "  2. Database connection issues"
	@echo "  3. Worker queue backlog"
	@echo ""
	@echo "Each scenario will simulate the issue in staging"
	@echo "and guide you through the response."
	@echo ""
	@echo "Start with: make incident-practice-latency"

incident-practice-latency: ## Practice latency incident response
	@echo "Starting latency practice scenario..."
	@echo "(This will temporarily slow staging API)"
	@./scripts/simulate-latency.sh
	@echo ""
	@echo "Now diagnose: make incident-api-latency"
	@echo "After diagnosis: make incident-practice-cleanup"
```

## Real-World Example: From Chaos to Runbooks

Let's look at a complete transformation from ad-hoc incident response to structured runbooks:

### Before: Incident Response via Slack

```
[2:15 AM] PagerDuty: High error rate on API
[2:17 AM] OnCall Engineer: Anyone know how to check the error logs?
[2:23 AM] OnCall Engineer: Found the logs but there are thousands of errors
[2:31 AM] Senior Engineer (awakened): Did you check the cache connection?
[2:33 AM] OnCall Engineer: How do I do that?
[2:35 AM] Senior Engineer: kubectl exec into a pod and curl the cache health endpoint
[2:40 AM] OnCall Engineer: Cache is timing out. Restart it?
[2:42 AM] Senior Engineer: Yeah, but make sure to restart the API pods after
[2:58 AM] OnCall Engineer: How do I restart the cache in production?
[3:15 AM] Incident resolved (MTTR: 60 minutes)
```

### After: Incident Response via Runbooks

```
[2:15 AM] PagerDuty: High error rate on API
[2:16 AM] OnCall Engineer: $ make incident-api-errors
  🔍 Analyzing error patterns...
  ❌ Cache connection failures detected (95% of errors)
  💡 Next step: make incident-cache-check
[2:17 AM] OnCall Engineer: $ make incident-cache-check
  🔍 Checking cache status...
  ❌ Cache health check failed
  ⚠️  Cache appears to be down
  💡 Resolution: make incident-cache-restart
[2:18 AM] OnCall Engineer: $ make incident-cache-restart
  ⚠️  About to restart production cache. Continue? [y/N] y
  Restarting cache...
  ✅ Cache restarted
  Restarting dependent services...
  ✅ All services restarted
  📊 Monitor: make health-check
[2:20 AM] OnCall Engineer: $ make health-check
  ✅ API: Healthy
  ✅ Database: Healthy  
  ✅ Cache: Healthy
[2:20 AM] Incident resolved (MTTR: 5 minutes)
```

Here's the Makefile that enabled this:

```makefile
# Production Incident Runbooks
.PHONY: incident-help incident-api-errors incident-cache-check

incident-help: ## Show available incident runbooks
	@echo "🚨 Incident Response Runbooks"
	@echo "============================="
	@echo ""
	@echo "Quick Start:"
	@echo "  make health-check          # Check system health"
	@echo "  make incident-api-errors   # High error rate"
	@echo "  make incident-api-latency  # High latency"
	@echo "  make incident-db-pool      # DB connection issues"
	@echo ""
	@echo "For complete list: make incident-list"

incident-api-errors: ## Diagnose high API error rate
	@echo "🔍 Analyzing error patterns..."
	@errors=$$(kubectl logs -n production deploy/api --since=5m | \
		grep ERROR | wc -l); \
	echo "Error count (last 5 min): $$errors"
	@echo ""
	@echo "Top error types:"
	@kubectl logs -n production deploy/api --since=5m | \
		grep ERROR | awk -F'[][]' '{print $$2}' | sort | uniq -c | \
		sort -rn | head -5
	@echo ""
	@cache_errors=$$(kubectl logs -n production deploy/api --since=5m | \
		grep -i "cache.*error\|redis.*error" | wc -l); \
	if [ $$cache_errors -gt 10 ]; then \
		echo "❌ Cache connection failures detected"; \
		echo "💡 Next step: make incident-cache-check"; \
	fi

incident-cache-check: ## Check cache health and connectivity
	@echo "🔍 Checking cache status..."
	@if kubectl exec -n production deploy/api-0 -- \
		timeout 2 redis-cli -h cache.prod.company.com ping \
		2>/dev/null | grep -q PONG; then \
		echo "✅ Cache responding normally"; \
	else \
		echo "❌ Cache health check failed"; \
		echo "⚠️  Cache appears to be down"; \
		echo "💡 Resolution: make incident-cache-restart"; \
	fi

incident-cache-restart: ## Restart cache and dependent services
	@echo "⚠️  About to restart production cache"
	@echo "This will cause brief service disruption."
	@echo -n "Continue? [y/N] " && read ans && [ $${ans:-N} = y ]
	@echo "Restarting cache..."
	@kubectl rollout restart -n production statefulset/cache
	@kubectl rollout status -n production statefulset/cache
	@echo "✅ Cache restarted"
	@echo "Restarting dependent services..."
	@kubectl rollout restart -n production deploy/api
	@kubectl rollout status -n production deploy/api
	@echo "✅ All services restarted"
	@echo "📊 Monitor: make health-check"
```

## Key Takeaways

Make-based incident response transforms how teams handle production issues:

1. **Discoverability**: New engineers can find and execute response procedures without prior knowledge
2. **Consistency**: Everyone follows the same diagnostic steps and resolution procedures
3. **Speed**: Reduced time searching for commands and procedures
4. **Safety**: Built-in validation and confirmation for destructive operations
5. **Learning**: Runbooks teach the system while solving problems
6. **Evolution**: Easy to update and improve based on new insights

The goal isn't to automate away human judgment—incidents often require creative problem-solving. Instead, Make-based runbooks handle the routine parts (finding logs, checking health, executing common fixes) so engineers can focus on the novel aspects of each incident.

Most importantly, these runbooks capture team lore in executable form. That 2 AM incident response knowledge that used to live only in senior engineers' heads now lives in version-controlled Make targets that anyone can execute, learn from, and improve.

In the next chapter, we'll explore how to apply similar patterns to security and compliance workflows, where discoverability and consistent execution are even more critical.