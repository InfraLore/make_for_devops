# Chapter 14: Make for Infrastructure Reliability

\chaptersubtitle{Building discoverable workflows for testing, recovery, and
maintaining healthy infrastructure.}

In the previous chapter, we explored how Make brings discoverability to
infrastructure provisioning—the act of creating and modifying infrastructure.
But provisioning is just the beginning. Once infrastructure exists, it needs
continuous care: testing to ensure it works, monitoring to detect problems,
procedures to recover from failures, and maintenance to prevent cost overruns.

These reliability workflows suffer from the same problems as provisioning:
scattered documentation, team lore, and ad-hoc procedures that vary by
engineer. The on-call engineer gets paged at 2 AM and needs to remember (or
frantically search Confluence for) the correct sequence of commands to restore a
failed database. The monthly cost review reveals mystery resources no one
remembers creating. The staging environment slowly drifts away from production
until they're fundamentally different systems.

Make's discovery patterns solve these problems by making reliability workflows
as discoverable as provisioning workflows. When something breaks, `make
emergency` shows you what to do. When costs spike, `make cleanup` reveals what
can be safely removed. When you wonder if infrastructure is healthy, `make
validate-all` tells you.

## The Infrastructure Reliability Challenge

Infrastructure reliability isn't about a single big event—it's about dozens of
small, regular tasks that keep systems healthy. Each of these tasks has a "right
way" to do it, but that knowledge often exists only in senior engineers' minds.

Consider a typical week in infrastructure operations:

**Monday**: "We should test our disaster recovery procedures. How do we do that
again?"

**Tuesday**: "Staging feels slow. How do we validate the infrastructure
configuration?"

**Wednesday**: "We got an alert about disk space. What's safe to clean up?"

**Thursday**: "Cost report shows $2000 in mystery charges. How do we track down
what's running?"

**Friday**: "We need to rotate database credentials. What's the procedure?"

Each of these has a solution, probably documented somewhere. But finding and
following that documentation takes time, and each engineer might do it slightly
differently. Worse, these procedures change as infrastructure evolves, but
documentation rarely keeps pace.

## Discovering Infrastructure Health

The first reliability pattern is making health checks discoverable:

```makefile
.DEFAULT_GOAL := health

health: ## Quick infrastructure health check
	@echo "Infrastructure Health - $(ENVIRONMENT)"
	@echo "====================================="
	@$(MAKE) _check-resources
	@$(MAKE) _check-costs
	@$(MAKE) _check-security
	@echo ""
	@echo "Detailed checks: make validate-all"

_check-resources:
	@echo ""
	@echo "Resources:"
	@./scripts/check-resource-health.sh $(ENVIRONMENT) \footnote{Script delegation pattern---see Chapter 21 for how this aids learning.}

_check-costs:
	@echo ""
	@echo "Costs (last 7 days):"
	@./scripts/check-recent-costs.sh $(ENVIRONMENT)

_check-security:
	@echo ""
	@echo "Security:"
	@./scripts/check-security-status.sh $(ENVIRONMENT)

validate-all: ## Comprehensive infrastructure validation
	@echo "Running full validation suite..."
	@$(MAKE) validate-configuration
	@$(MAKE) validate-connectivity
	@$(MAKE) validate-performance
	@$(MAKE) validate-security
	@$(MAKE) validate-compliance
	@echo ""
	@echo "All validations passed"
```

Now when someone wonders "Is our infrastructure healthy?", they run `make
health` and get an immediate overview. If they need more detail, the output
tells them: `make validate-all`.

## Discovering Test Workflows

Infrastructure testing should be as discoverable as application testing:

```makefile
test: ## Run infrastructure tests
	@echo "What would you like to test?"
	@echo ""
	@echo "  make test-config          - Validate configurations"
	@echo "  make test-connectivity    - Test network connectivity"
	@echo "  make test-dr              - Test disaster recovery"
	@echo "  make test-performance     - Run performance tests"
	@echo ""
	@echo "  make test-all             - Run all tests"

test-config: ## Validate infrastructure configuration
	@echo "Validating configuration..."
	@terraform validate
	@./scripts/validate-configs.sh $(ENVIRONMENT)
	@echo "Configuration valid"

test-connectivity: ## Test network connectivity
	@echo "Testing connectivity..."
	@./scripts/test-connectivity.sh $(ENVIRONMENT)
	@echo "Connectivity tests passed"

test-dr: ## Test disaster recovery procedures
	@echo "Testing disaster recovery..."
	@echo ""
	@echo "This will:"
	@echo "  1. Create isolated test environment"
	@echo "  2. Simulate failure scenarios"
	@echo "  3. Validate recovery procedures"
	@echo "  4. Clean up test resources"
	@echo ""
	@echo -n "Continue? [y/N] " && read ans && [ $${ans:-N} = y ]
	@./scripts/test-disaster-recovery.sh $(ENVIRONMENT)
```

The `test` target without arguments becomes a menu that teaches what's testable.
Each test target is self-contained and can run independently.

## Discovering Disaster Recovery

When disaster strikes, discoverability becomes critical:

```makefile
recover: ## Show recovery procedures
	@echo "Infrastructure Recovery"
	@echo "========================="
	@echo ""
	@echo "What failed?"
	@echo "  make recover-database     - Database recovery"
	@echo "  make recover-application  - Application recovery"
	@echo "  make recover-network      - Network recovery"
	@echo "  make recover-complete     - Complete system recovery"
	@echo ""
	@echo "Status checks:"
	@echo "  make diagnose             - Diagnose current issues"

recover-database: ## Recover database from backup
	@echo "Database Recovery - $(ENVIRONMENT)"
	@echo "=================================="
	@echo ""
	@./scripts/list-backups.sh $(ENVIRONMENT) database
	@echo ""
	@echo -n "Backup to restore (or 'latest'): " && read backup && \
		./scripts/recover-database.sh $(ENVIRONMENT) $$backup
	@echo ""
	@echo "Next: make verify-database"

verify-database: ## Verify database recovery
	@echo "Verifying database health..."
	@./scripts/verify-database.sh $(ENVIRONMENT)

diagnose: ## Diagnose infrastructure issues
	@echo "Running diagnostics..."
	@./scripts/diagnose-issues.sh $(ENVIRONMENT)
	@echo ""
	@echo "Suggested recovery: [based on diagnostics output]"
```

The pattern creates a conversation: `make recover` asks what failed, then
provides specific recovery targets. Each recovery procedure includes
verification steps.

## Discovering Backup Workflows

Backups need to be automatic but also discoverable for manual operations:

```makefile
backup: ## Show backup operations
	@echo "Backup Operations"
	@echo "================="
	@echo ""
	@echo "Create backups:"
	@echo "  make backup-database      - Backup all databases"
	@echo "  make backup-state         - Backup Terraform state"
	@echo "  make backup-configs       - Backup configurations"
	@echo "  make backup-all           - Backup everything"
	@echo ""
	@echo "Manage backups:"
	@echo "  make list-backups         - List available backups"
	@echo "  make verify-backups       - Verify backup integrity"
	@echo "  make cleanup-old-backups  - Remove old backups"

backup-database: ## Create database backup
	@echo "Backing up databases..."
	@./scripts/backup-databases.sh $(ENVIRONMENT)
	@echo "Backup complete: backups/$(ENVIRONMENT)-$(date +%Y%m%d)"

list-backups: ## List available backups
	@echo "Available Backups - $(ENVIRONMENT)"
	@echo "=================================="
	@./scripts/list-backups.sh $(ENVIRONMENT) all

verify-backups: ## Verify backup integrity
	@echo "Verifying backup integrity..."
	@./scripts/verify-backups.sh $(ENVIRONMENT)
```

Running `make backup` shows what can be backed up. Running `make list-backups`
shows what exists. The workflow is discoverable without requiring backup
procedure documentation.

## Discovering Cost Management

Cost management is ongoing infrastructure work that needs discoverable workflows:

```makefile
costs: ## Show cost management operations
	@echo "Cost Management"
	@echo "==============="
	@echo ""
	@echo "Analysis:"
	@echo "  make cost-report          - Current costs by service"
	@echo "  make cost-trend           - Cost trends over time"
	@echo "  make cost-anomalies       - Detect unusual spending"
	@echo ""
	@echo "Optimization:"
	@echo "  make find-waste           - Find unused resources"
	@echo "  make cleanup-suggestions  - Get cleanup recommendations"
	@echo "  make cleanup-safe         - Remove safe-to-delete resources"

find-waste: ## Find unused or underutilized resources
	@echo "Scanning for waste..."
	@./scripts/find-waste.sh $(ENVIRONMENT)

cleanup-suggestions: ## Get cleanup recommendations
	@echo "Cleanup Suggestions - $(ENVIRONMENT)"
	@echo "===================================="
	@./scripts/cleanup-suggestions.sh $(ENVIRONMENT)
	@echo ""
	@echo "To clean up: make cleanup-safe"

cleanup-safe: ## Clean up safe-to-delete resources
	@echo "Safe Cleanup - $(ENVIRONMENT)"
	@./scripts/cleanup-safe.sh $(ENVIRONMENT)
	@echo ""
	@echo "Estimated monthly savings: [calculated amount]"
```

When the monthly cost report arrives, `make costs` shows what's available. `make
find-waste` identifies problems. `make cleanup-safe` fixes them.

## Discovering Maintenance Windows

Infrastructure maintenance needs scheduling and coordination:

```makefile
maintenance: ## Show maintenance operations
	@echo "Maintenance Operations"
	@echo "====================="
	@echo ""
	@echo "Regular maintenance:"
	@echo "  make maint-updates        - Apply system updates"
	@echo "  make maint-rotate-creds   - Rotate credentials"
	@echo "  make maint-cleanup        - Routine cleanup"
	@echo "  make maint-all            - Full maintenance"
	@echo ""
	@echo "Scheduled:"
	@echo "  make schedule-maintenance - Schedule maintenance window"

maint-updates: ## Apply system updates
	@echo "Maintenance: System Updates"
	@echo "Environment: $(ENVIRONMENT)"
	@echo ""
	@./scripts/check-update-impact.sh $(ENVIRONMENT)
	@echo ""
	@echo -n "Proceed with updates? [y/N] " && read ans && \
		[ $${ans:-N} = y ]
	@./scripts/apply-updates.sh $(ENVIRONMENT)

maint-rotate-creds: ## Rotate credentials
	@echo "Credential Rotation - $(ENVIRONMENT)"
	@./scripts/rotate-credentials.sh $(ENVIRONMENT)
	@echo "Credentials rotated"

maint-all: ## Full maintenance procedure
	@echo "Full Maintenance - $(ENVIRONMENT)"
	@echo "================================="
	@$(MAKE) backup-all
	@$(MAKE) maint-updates
	@$(MAKE) maint-rotate-creds
	@$(MAKE) maint-cleanup
	@$(MAKE) validate-all
	@echo "Maintenance complete"
```

The maintenance workflow is discoverable and can run manually or be scheduled.
Each step can also run independently.

## Discovering Monitoring and Alerts

Infrastructure reliability depends on monitoring. Make monitoring operations
discoverable:

```makefile
monitor: ## Monitoring operations
	@echo "Monitoring Operations"
	@echo "===================="
	@echo ""
	@echo "Current status:"
	@echo "  make alerts               - Check active alerts"
	@echo "  make metrics              - Key metrics dashboard"
	@echo ""
	@echo "Configuration:"
	@echo "  make setup-monitoring     - Deploy monitoring stack"
	@echo "  make test-alerts          - Test alert configuration"

alerts: ## Show active alerts
	@echo "Active Alerts - $(ENVIRONMENT)"
	@./scripts/check-alerts.sh $(ENVIRONMENT)

metrics: ## Show key metrics
	@echo "Key Metrics - $(ENVIRONMENT)"
	@./scripts/show-metrics.sh $(ENVIRONMENT)

test-alerts: ## Test alert configuration
	@echo "Testing alert configuration..."
	@./scripts/test-alerts.sh $(ENVIRONMENT)
	@echo "Alert tests passed"
```

## Discovering Through Scheduled Operations

Some reliability tasks should run automatically but need to be discoverable for
manual execution:

```makefile
scheduled: ## Show scheduled operations
	@echo "Scheduled Operations"
	@echo "==================="
	@echo ""
	@echo "Daily:"
	@echo "  make daily-checks         - Health and security checks"
	@echo "  make daily-backup         - Automated backups"
	@echo ""
	@echo "Weekly:"
	@echo "  make weekly-maintenance   - Routine maintenance"
	@echo "  make weekly-cost-review   - Cost analysis"
	@echo ""
	@echo "Monthly:"
	@echo "  make monthly-dr-test      - DR testing"
	@echo "  make monthly-audit        - Compliance audit"

daily-checks: ## Run daily health checks
	@$(MAKE) health
	@$(MAKE) validate-security
	@$(MAKE) check-drift

weekly-maintenance: ## Run weekly maintenance
	@$(MAKE) cleanup-old-resources
	@$(MAKE) rotate-logs
	@$(MAKE) update-monitoring-dashboards

monthly-dr-test: ## Run monthly DR test
	@echo "Monthly DR Test - $(ENVIRONMENT)"
	@./scripts/monthly-dr-test.sh $(ENVIRONMENT)
```

Engineers can run these manually when needed, but they also document what
automation should do.

## Real-World Reliability Discovery Story

A platform team maintained a 30-page "Infrastructure Operations Runbook" with
sections like:

```markdown
# Database Recovery Procedure

Prerequisites:
- Access to AWS console
- Database backup location documented
- Recovery time objective: 4 hours

Steps:
1. Identify the backup to restore...
   [detailed steps]
2. Stop the application servers...
   [more steps]
3. Restore the database...
   [even more steps]
...

# Cost Cleanup Procedure

Run quarterly. Steps:
1. Generate cost report...
2. Identify unused resources...
3. Verify with team leads...
...
```

Problems:

- Runbook was always outdated
- 2 AM incidents meant searching through 30 pages
- Different engineers followed different steps
- No way to know if procedures still worked

After implementing discovery patterns:

```bash
# 2 AM page about database failure
$ make recover
Infrastructure Recovery
=========================

What failed?
  make recover-database     - Database recovery
  make recover-application  - Application recovery
  ...

$ make recover-database
Database Recovery - production
==================================

Available backups:
  latest (2 hours ago)
  backup-20240115-0200 (2 hours ago)
  backup-20240115-0000 (4 hours ago)

Backup to restore (or 'latest'): latest

[Recovery proceeds with clear feedback at each step]

Next: make verify-database

$ make verify-database
Verifying database health...
Database responding
Replication healthy
Connections normal

Recovery complete!
```

Results:

- Mean time to recovery decreased from 90 minutes to 20 minutes
- Runbook reduced to: "Run `make recover`"
- Procedures tested monthly (automated)
- Junior engineers handled incidents confidently

The discovery pattern worked because it guided engineers through the crisis
rather than requiring them to remember complex procedures under pressure.

## Key Takeaways

Infrastructure reliability becomes discoverable through Make by:

1. **Health as a command**: `make health` immediately shows infrastructure
   status
2. **Contextual menus**: Running `make recover` or `make backup` shows relevant
   options
3. **Guided workflows**: Each step suggests the next step
4. **Self-contained operations**: Each reliability task is independently
   runnable
5. **Built-in verification**: Recovery procedures include validation steps

The pattern transforms reliability from "remember the procedure" to "ask Make
what to do." This works especially well for reliability because:

- These tasks are infrequent (you don't remember the steps)
- They're often urgent (no time to search documentation)
- They need to be correct (mistakes have consequences)
- They change as infrastructure evolves (documentation drifts)

By making reliability workflows discoverable, Make ensures that critical
procedures are always accessible, always current, and always guide engineers
toward successful outcomes—whether it's 2 PM or 2 AM.

In the next chapter, we'll extend these patterns to monitoring and metrics,
exploring how Make can orchestrate observability workflows that keep your
systems transparent and understandable.
