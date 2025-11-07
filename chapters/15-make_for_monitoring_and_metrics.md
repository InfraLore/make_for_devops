# Chapter 15 - Make for Monitoring and Metrics

\chaptersubtitle{Bridging local and remote workflows with consistent,
discoverable automation.}

At 3 AM, your phone buzzes with an alert. The API response time has spiked to 2
seconds. Half-awake, you need to check metrics, compare them to baseline, maybe
adjust alert thresholds, and document what you find. You fumble through
bookmarked Grafana URLs, try to remember the Prometheus query syntax, and
eventually cobble together enough information to decide it's a false alarm
caused by a batch job.

The next morning, a colleague asks: "How do I check if our database connection
pool is healthy?" You realize that the ad-hoc investigation you did at 3 AM—the
queries you ran, the dashboards you checked, the metrics you compared—exists
only in your browser history and fading memory.

This scenario reveals a fundamental gap in how most teams handle observability.
We invest heavily in monitoring infrastructure—Prometheus, Grafana, DataDog, New
Relic—but the **workflows for interacting with that infrastructure** remain
undocumented, scattered across wiki pages, or locked in senior engineers' minds.

## The Observability Workflow Problem

Modern monitoring stacks are powerful but complex. A typical setup might include:

- Prometheus for metrics collection
- Grafana for visualization
- Alertmanager for alert routing
- Custom exporters for application metrics
- Service level indicators (SLIs) and objectives (SLOs)
- Performance testing tools
- Log aggregation systems

Each tool has its own interface, query language, and configuration format.
Common tasks like "check if the deployment improved performance" or "validate
that our SLOs are being met" require coordinating multiple tools and remembering
specific queries or dashboard URLs.

The knowledge gap manifests in several ways:

**The Discovery Problem**: New team members don't know what metrics are
available or how to access them. They don't know which Grafana dashboards to
check for different scenarios or what Prometheus queries reveal the health of
each service.

**The Consistency Problem**: Different engineers check different metrics when
investigating issues. One person looks at CPU and memory, another checks request
rates and error rates, a third examines database query times. Without a shared
workflow, investigations lack consistency.

**The Documentation Problem**: Wiki pages describe what metrics exist but not
how to use them operationally. They show example queries but don't explain when
to run them or how to interpret the results.

**The Integration Problem**: Monitoring is often treated as separate from
development and deployment workflows. Developers deploy code without checking
metrics, or check metrics manually rather than as part of an automated workflow.

Make can transform how teams interact with their monitoring infrastructure by
creating **discoverable, executable monitoring workflows**.

## Designing Discoverable Monitoring Workflows

The key insight is that common monitoring tasks should be as easy to discover
and execute as running `make test`. Instead of remembering Prometheus query
syntax or bookmarking Grafana URLs, engineers should be able to run commands
like:

```bash
make metrics-api          # Show key API metrics
make check-slos           # Verify we're meeting SLOs
make compare-performance  # Compare current vs baseline
make metrics-help         # Learn what's available
```

Let's start with a basic pattern for making metrics discoverable:

```makefile
.PHONY: metrics-help metrics-api metrics-db metrics-cache

metrics-help: ## Show available monitoring commands
	@echo "Monitoring & Metrics Commands"
	@echo "============================"
	@echo ""
	@echo "Quick Health Checks:"
	@echo "  make metrics-api       - API performance metrics"
	@echo "  make metrics-db        - Database health metrics"
	@echo "  make metrics-cache     - Cache hit rates"
	@echo ""
	@echo "SLO Validation:"
	@echo "  make check-slos        - Verify SLO compliance"
	@echo "  make slo-report        - Generate SLO report"
	@echo ""
	@echo "Dashboards:"
	@echo "  make dashboard-api     - Open API dashboard"
	@echo "  make dashboard-infra   - Open infrastructure dashboard"

metrics-api: ## Show API performance metrics (last 5m)
	@echo "API Metrics (last 5 minutes)"
	@echo "============================"
	@./scripts/prometheus-query.sh \ \footnote{Script delegation pattern---see Chapter 21 for how this aids learning.}
	  'rate(http_requests_total[5m])' \
	  "Request rate"
	@./scripts/prometheus-query.sh \
	  'histogram_quantile(0.95, http_request_duration_seconds)' \
	  "P95 latency"
	@./scripts/prometheus-query.sh \
	  'rate(http_requests_total{status=~"5.."}[5m])' \
	  "Error rate"
```

This pattern makes monitoring workflows discoverable through the same interface
engineers already use for development tasks. The `metrics-help` target acts as a
menu of available monitoring capabilities, and individual targets provide
focused, actionable information.

## Self-Documenting Metric Queries

One challenge with monitoring tools is that queries often lack context. A
Prometheus query like `rate(http_requests_total[5m])` tells you the request
rate, but not what that number means operationally—what's normal, what's
concerning, or what to do if it's outside expected ranges.

Make targets can embed this operational context:

```makefile
metrics-api-detailed: ## Detailed API health check with context
	@echo "API Health Check - $(shell date)"
	@echo "================================"
	@echo ""
	@echo "1. Request Rate (expect: 100-500 req/s)"
	@RATE=$$(./scripts/prometheus-query.sh \
	  'rate(http_requests_total[5m])' --value-only); \
	echo "   Current: $$RATE req/s"; \
	if [ $$(echo "$$RATE < 100" | bc) -eq 1 ]; then \
	  echo "   Lower than expected"; \
	elif [ $$(echo "$$RATE > 500" | bc) -eq 1 ]; then \
	  echo "   Higher than expected"; \
	else \
	  echo "   Normal"; \
	fi
	@echo ""
	@echo "2. P95 Latency (SLO: < 200ms)"
	@LATENCY=$$(./scripts/prometheus-query.sh \
	  'histogram_quantile(0.95, http_request_duration_seconds)' \
	  --value-only); \
	echo "   Current: $$LATENCY ms"; \
	if [ $$(echo "$$LATENCY > 200" | bc) -eq 1 ]; then \
	  echo "   SLO violation - Check 'make debug-latency'"; \
	else \
	  echo "   Meeting SLO"; \
	fi
	@echo ""
	@echo "3. Error Rate (SLO: < 0.1%)"
	@./scripts/check-error-rate.sh
```

Now when an engineer runs `make metrics-api-detailed`, they get not just raw
numbers but interpreted results with operational context. The target tells them
what's normal, what's concerning, and what to do next.

## Monitoring Stack Deployment as Discoverable Workflow

Deploying and configuring monitoring infrastructure is itself a complex workflow
that benefits from the Executable README approach. Instead of lengthy
documentation about setting up Prometheus, Grafana, and exporters, teams can
encode the entire process:

```makefile
.PHONY: monitoring-setup monitoring-status

monitoring-setup: ## Deploy complete monitoring stack
	@echo "Deploying monitoring infrastructure..."
	@$(MAKE) deploy-prometheus
	@$(MAKE) deploy-grafana
	@$(MAKE) deploy-exporters
	@$(MAKE) configure-dashboards
	@$(MAKE) configure-alerts
	@echo ""
	@echo "Monitoring stack deployed!"
	@echo ""
	@echo "Next steps:"
	@echo "  make monitoring-status  - Check stack health"
	@echo "  make dashboard-open     - Open Grafana"
	@echo "  make test-alerts        - Test alert routing"

deploy-prometheus: ## Deploy Prometheus server
	@echo "→ Deploying Prometheus..."
	@kubectl apply -f k8s/monitoring/prometheus/
	@kubectl rollout status statefulset/prometheus -n monitoring
	@echo "  Prometheus ready"

deploy-grafana: ## Deploy Grafana with preconfigured dashboards
	@echo "→ Deploying Grafana..."
	@kubectl apply -f k8s/monitoring/grafana/
	@kubectl rollout status deployment/grafana -n monitoring
	@echo "  Grafana ready"

configure-dashboards: ## Import Grafana dashboards
	@echo "→ Configuring dashboards..."
	@./scripts/import-grafana-dashboards.sh
	@echo "  Dashboards configured"

monitoring-status: ## Check monitoring stack health
	@echo "Monitoring Stack Status"
	@echo "======================"
	@kubectl get pods -n monitoring
	@echo ""
	@echo "Prometheus: http://prometheus.local"
	@echo "Grafana:    http://grafana.local (admin/$(GRAFANA_PASSWORD))"
```

The `monitoring-setup` target acts as executable documentation for the entire
deployment process. A new team member or a disaster recovery scenario becomes
simply: `make monitoring-setup` followed by `make monitoring-status`.

## Performance Testing as Documented Workflow

Performance testing often suffers from the same institutional knowledge problem
as monitoring. Engineers know they should test performance before releases, but
the specifics—what to test, how to interpret results, what thresholds
matter—remain undocumented.

Make can transform performance testing into a discoverable, repeatable workflow:

```makefile
.PHONY: perf-test perf-baseline perf-compare

perf-test: ## Run performance test suite
	@echo "Running performance tests against $(ENVIRONMENT)..."
	@$(MAKE) perf-api-load
	@$(MAKE) perf-api-spike
	@$(MAKE) perf-db-queries
	@$(MAKE) perf-report

perf-api-load: ## Load test: sustained traffic
	@echo "→ Load test (10 min, 100 req/s)..."
	@k6 run --duration 10m --rps 100 \
	  tests/performance/api-load.js
	@echo "  Load test complete"

perf-api-spike: ## Spike test: traffic burst
	@echo "→ Spike test (2 min, 500 req/s)..."
	@k6 run --duration 2m --rps 500 \
	  tests/performance/api-spike.js
	@echo "  Spike test complete"

perf-baseline: ## Capture performance baseline
	@echo "Capturing performance baseline..."
	@$(MAKE) perf-test ENVIRONMENT=staging
	@./scripts/save-baseline.sh
	@echo "Baseline saved to baselines/$(VERSION).json"

perf-compare: ## Compare current performance to baseline
	@echo "Comparing performance to baseline..."
	@$(MAKE) perf-test ENVIRONMENT=staging
	@./scripts/compare-to-baseline.sh
	@echo ""
	@echo "Key Changes:"
	@echo "  P95 Latency: $(P95_CHANGE)%"
	@echo "  Throughput:  $(THROUGHPUT_CHANGE)%"
	@echo "  Error Rate:  $(ERROR_CHANGE)%"
```

This approach makes performance testing a natural part of the development
workflow. Before a release, an engineer runs `make perf-compare` to see if the
changes improved or degraded performance. The results are automatically compared
to baseline, and the workflow is documented through its execution.

## SLO Monitoring as Executable Documentation

Service Level Objectives (SLOs) are commitments about system performance, but
tracking them often involves manual dashboard checking or complex queries. Make
can turn SLO monitoring into a simple, discoverable workflow:

```makefile
.PHONY: check-slos slo-report slo-budget

check-slos: ## Quick SLO compliance check
	@echo "SLO Compliance Check"
	@echo "==================="
	@echo ""
	@$(MAKE) --no-print-directory check-slo-availability
	@$(MAKE) --no-print-directory check-slo-latency
	@$(MAKE) --no-print-directory check-slo-errors

check-slo-availability: ## Check availability SLO (99.9%)
	@printf "Availability (99.9%% SLO): "
	@UPTIME=$$(./scripts/calculate-uptime.sh 30d); \
	if [ $$(echo "$$UPTIME >= 99.9" | bc) -eq 1 ]; then \
	  echo "$$UPTIME%% (meeting SLO)"; \
	else \
	  echo "$$UPTIME%% (SLO violation)"; \
	fi

check-slo-latency: ## Check latency SLO (P95 < 200ms)
	@printf "P95 Latency (200ms SLO):   "
	@LATENCY=$$(./scripts/calculate-p95.sh 30d); \
	if [ $$(echo "$$LATENCY < 200" | bc) -eq 1 ]; then \
	  echo "$${LATENCY}ms (meeting SLO)"; \
	else \
	  echo "$${LATENCY}ms (SLO violation)"; \
	fi

slo-budget: ## Show remaining error budget
	@echo "Error Budget Status (30 day window)"
	@echo "==================================="
	@./scripts/calculate-error-budget.sh
	@echo ""
	@echo "Interpretation:"
	@echo "  >50%% remaining: Safe to take risks"
	@echo "  10-50%% remaining: Be cautious"
	@echo "  <10%% remaining: Focus on reliability"
```

Now checking SLO compliance is as simple as `make check-slos`. The target
provides immediate, actionable feedback about whether the system is meeting its
commitments, and `make slo-budget` shows how much error budget remains—crucial
information for balancing feature velocity with reliability.

## Alert Configuration as Discoverable Workflow

Alert configuration is notoriously difficult to get right. Alerts need to be
sensitive enough to catch real issues but not so noisy that they get ignored.
The process of creating, testing, and refining alerts is often undocumented.

Make can make alert management discoverable and testable:

```makefile
.PHONY: alerts-deploy alerts-test alerts-validate

alerts-deploy: ## Deploy alert rules
	@echo "Deploying alert rules..."
	@$(MAKE) alerts-validate
	@kubectl apply -f monitoring/alerts/
	@echo "Alert rules deployed"
	@echo ""
	@echo "Test alerts with: make alerts-test"

alerts-validate: ## Validate alert rule syntax
	@echo "Validating alert rules..."
	@promtool check rules monitoring/alerts/*.yml
	@echo "Alert rules valid"

alerts-test: ## Test alert delivery
	@echo "Testing alert routing..."
	@echo ""
	@echo "1. Testing critical alert..."
	@./scripts/trigger-test-alert.sh critical
	@echo "   Check #incidents channel for alert"
	@echo ""
	@echo "2. Testing warning alert..."
	@./scripts/trigger-test-alert.sh warning
	@echo "   Check #alerts channel for alert"

alerts-silence: ## Create maintenance window silence
	@echo "Creating maintenance silence..."
	@read -p "Duration (e.g., 2h): " DURATION; \
	./scripts/create-silence.sh $$DURATION
	@echo "Alerts silenced"
```

The `alerts-test` target is particularly valuable—it allows engineers to verify
that alerts are actually reaching the right channels before an incident occurs.
Testing becomes a documented, repeatable workflow rather than ad-hoc manual
verification.

## Dashboard Management as Code

Grafana dashboards are often created through the UI and never properly version
controlled or documented. Make can bring dashboard configuration into the same
workflow as code:

```makefile
.PHONY: dashboard-export dashboard-import dashboard-open

dashboard-export: ## Export dashboard for version control
	@echo "Exporting dashboards from Grafana..."
	@./scripts/export-grafana-dashboards.sh
	@echo "Dashboards exported to dashboards/"

dashboard-import: ## Import dashboards to Grafana
	@echo "Importing dashboards to Grafana..."
	@./scripts/import-grafana-dashboards.sh
	@echo "Dashboards imported"

dashboard-open: ## Open dashboards in browser
	@echo "Available dashboards:"
	@echo "  1. API Overview"
	@echo "  2. Infrastructure Health"
	@echo "  3. Database Performance"
	@echo "  4. SLO Dashboard"
	@read -p "Choose [1-4]: " CHOICE; \
	./scripts/open-dashboard.sh $$CHOICE

dashboard-create-api: ## Create new API service dashboard
	@echo "Creating dashboard for new API service..."
	@read -p "Service name: " SERVICE; \
	./scripts/create-dashboard.sh api $$SERVICE
	@echo "Dashboard created"
	@echo "  View: make dashboard-open"
```

This pattern brings dashboard management into the standard development workflow.
When a new service is deployed, creating its dashboard becomes `make
dashboard-create-api` rather than a manual, undocumented process in the Grafana
UI.

## Integrating Monitoring with Development Workflow

The real power of Make-based monitoring workflows emerges when monitoring
becomes integrated with development and deployment. Instead of monitoring being
a separate concern, it becomes part of the standard workflow:

```makefile
.PHONY: deploy-with-monitoring deploy-dev

deploy-dev: ## Deploy to dev with monitoring checks
	@echo "Deploying to development environment..."
	@$(MAKE) build
	@$(MAKE) test
	@$(MAKE) perf-baseline ENVIRONMENT=dev-before
	@./scripts/deploy.sh dev
	@echo "Waiting for deployment to stabilize (30s)..."
	@sleep 30
	@$(MAKE) metrics-api ENVIRONMENT=dev
	@$(MAKE) perf-compare ENVIRONMENT=dev
	@echo ""
	@echo "Deployment complete with monitoring validation"

deploy-staging: ## Deploy to staging with full validation
	@$(MAKE) deploy-with-monitoring ENVIRONMENT=staging
	@$(MAKE) check-slos ENVIRONMENT=staging
	@$(MAKE) alerts-test ENVIRONMENT=staging

deploy-with-monitoring: check-metrics-baseline
	@echo "Deploying $(VERSION) to $(ENVIRONMENT)..."
	@./scripts/deploy.sh $(ENVIRONMENT)
	@echo "Monitoring deployment impact..."
	@$(MAKE) wait-for-stability
	@$(MAKE) compare-metrics

check-metrics-baseline: ## Capture pre-deployment metrics
	@echo "Capturing baseline metrics..."
	@./scripts/capture-metrics.sh $(ENVIRONMENT) pre-deploy

compare-metrics: ## Compare post-deployment to baseline
	@echo "Comparing metrics to baseline..."
	@./scripts/compare-metrics.sh $(ENVIRONMENT)
```

Now deployment inherently includes monitoring validation. An engineer deploying
to development automatically sees how the change affects performance metrics.
This tight integration between deployment and monitoring makes performance
regressions immediately visible.

## Real-World Example: Monitoring Stack Setup

Let's look at a complete example that ties these concepts together—setting up
monitoring for a microservices application:

```makefile
# Monitoring and Metrics Workflow
PROMETHEUS_URL ?= http://prometheus.monitoring.svc:9090
GRAFANA_URL ?= http://grafana.monitoring.svc:3000
ENVIRONMENT ?= production

.PHONY: monitoring-help monitoring-setup monitoring-status

monitoring-help: ## Show monitoring commands
	@echo "Monitoring Commands"
	@echo "=================="
	@echo ""
	@echo "Setup:"
	@echo "  make monitoring-setup    - Deploy monitoring stack"
	@echo "  make monitoring-status   - Check stack health"
	@echo ""
	@echo "Metrics:"
	@echo "  make metrics            - Show key metrics"
	@echo "  make check-slos         - Verify SLO compliance"
	@echo ""
	@echo "Performance:"
	@echo "  make perf-test          - Run performance tests"
	@echo "  make perf-compare       - Compare to baseline"
	@echo ""
	@echo "Dashboards:"
	@echo "  make dashboard-open     - Open Grafana dashboards"

monitoring-setup: ## Deploy complete monitoring stack
	@echo "Setting up monitoring infrastructure..."
	@$(MAKE) check-monitoring-prerequisites
	@$(MAKE) deploy-prometheus
	@$(MAKE) deploy-grafana
	@$(MAKE) configure-dashboards
	@$(MAKE) deploy-exporters
	@$(MAKE) configure-alerts
	@echo ""
	@echo "Monitoring stack ready!"
	@echo ""
	@$(MAKE) monitoring-status

check-monitoring-prerequisites:
	@echo "→ Checking prerequisites..."
	@kubectl get namespace monitoring >/dev/null 2>&1 || \
	  kubectl create namespace monitoring
	@echo "  Prerequisites met"

deploy-prometheus:
	@echo "→ Deploying Prometheus..."
	@kubectl apply -f k8s/monitoring/prometheus/ -n monitoring
	@echo "  Prometheus deployed"

deploy-grafana:
	@echo "→ Deploying Grafana..."
	@kubectl apply -f k8s/monitoring/grafana/ -n monitoring
	@echo "  Grafana deployed"

metrics: ## Show current system metrics
	@echo "System Metrics - $(ENVIRONMENT)"
	@echo "=============================="
	@$(MAKE) --no-print-directory metrics-api
	@echo ""
	@$(MAKE) --no-print-directory metrics-db
	@echo ""
	@$(MAKE) --no-print-directory check-slos

metrics-api:
	@echo "API Metrics (5 min average):"
	@./scripts/show-metric.sh request_rate
	@./scripts/show-metric.sh p95_latency
	@./scripts/show-metric.sh error_rate

dashboard-open: ## Open monitoring dashboards
	@echo "Opening Grafana dashboards..."
	@open "$(GRAFANA_URL)/d/api-overview"
	@echo "Dashboard opened in browser"
```

## Integration with Incident Response

Monitoring workflows naturally extend into incident response. When an alert
fires, the same Make-based approach provides discoverable runbooks:

```makefile
.PHONY: incident-check incident-debug

incident-check: ## Quick health check for incident response
	@echo "Incident Response Health Check"
	@echo "============================="
	@echo ""
	@$(MAKE) --no-print-directory check-slos
	@echo ""
	@$(MAKE) --no-print-directory metrics
	@echo ""
	@echo "Recent alerts:"
	@./scripts/show-recent-alerts.sh

incident-debug-latency: ## Debug high latency incident
	@echo "Debugging Latency Issue"
	@echo "======================"
	@echo ""
	@echo "1. Checking database query times..."
	@./scripts/check-slow-queries.sh
	@echo ""
	@echo "2. Checking external API latency..."
	@./scripts/check-external-apis.sh
	@echo ""
	@echo "3. Checking cache hit rate..."
	@./scripts/check-cache-performance.sh
```

When someone is paged at 3 AM, they can run `make incident-check` to get a
comprehensive view of system health, then `make incident-debug-latency` to
follow a structured debugging workflow. The response is consistent across team
members and the steps are documented through execution.

## Key Takeaways

Treating monitoring and metrics as discoverable Make workflows solves several
critical problems:

1. **Discoverability**: New team members can run `make monitoring-help` to learn
   what monitoring capabilities exist
2. **Consistency**: Everyone uses the same queries and checks the same metrics
3. **Context**: Metrics include operational context about what's normal and what
   to do when things are abnormal
4. **Integration**: Monitoring becomes part of the standard development
   workflow, not a separate concern
5. **Documentation**: The workflows themselves document how to interact with
   monitoring infrastructure

The key is designing monitoring workflows that are:

- **Immediately useful**: Running a target provides actionable information
- **Self-documenting**: Targets include context about what results mean
- **Composable**: Complex checks built from simple, focused targets
- **Integrated**: Monitoring naturally flows into development and deployment

In the next chapter, we'll explore how Make brings the same discoverability
benefits to logging and incident response, completing the observability picture
with structured approaches to debugging and emergency response.
