# Chapter 17: Security and Compliance Workflows

\chaptersubtitle{Making security scanners discoverable, compliance checks repeatable, and audit trails automatic.}

Your company just landed a major enterprise client, but there’s a catch: they require SOC 2 Type II compliance, quarterly security audits, and evidence that you’re running vulnerability scans before every deployment. The security team sends you a 47-page compliance checklist. You need to prove that you scan container images, rotate secrets monthly, validate TLS certificates, check for exposed credentials, maintain audit logs, and document all configuration changes.

You look at your deployment pipeline. It works—containers build, tests pass, deployments succeed. But security scanning? That’s a manual step someone runs “when they remember.” Secret rotation happens “sometime” using a process that’s different for each service. Audit logs exist somewhere, but nobody’s sure how to query them.

The security team’s recommendation: “Add security scanning tools to your pipeline.” This sounds simple until you discover there are dozens of tools—Trivy, Snyk, Grype for containers; TruffleHog, git-secrets for credential scanning; tfsec, Checkov for infrastructure; gosec, bandit, semgrep for code. Each has different installation procedures, configuration files, output formats, and failure criteria.

This is where most teams make a critical mistake: they add the tools but don’t make them **discoverable or repeatable**. Security scanning becomes something that “happens in CI” but nobody knows how to run locally, interpret results, or fix issues.

Make offers a better approach: **security and compliance as discoverable workflows**.

## The Problem with Hidden Security

Traditional security integration follows a pattern: the security team mandates a tool, someone adds it to the CI pipeline, and it becomes an invisible step that either passes or fails mysteriously. Developers encounter security failures like this:

```
Build failed: Security scan detected vulnerabilities
See: https://ci.company.com/build/12847/security-scan
```

They click the link, see a wall of JSON output, and now what? Which vulnerabilities are critical? How do they fix them? Can they test the fix locally?

Here’s the discovery-based approach:

```makefile
.PHONY: security-check security-scan-containers security-scan-code

security-check: ## Run all security scans
	@echo "Running security checks..."
	@$(MAKE) -s security-scan-containers || exit 1
	@$(MAKE) -s security-scan-code || exit 1
	@$(MAKE) -s security-scan-secrets || exit 1
	@echo "All security checks passed"

security-scan-containers: ## Scan container images
	@echo "Scanning container images..."
	@./scripts/scan-containers.sh $(IMAGE_NAME) || \ 
		(echo "Fix: make security-fix-containers" && exit 1)

security-scan-code: ## Scan code for vulnerabilities
	@echo "Scanning code..."
	@./scripts/scan-code.sh || \
		(echo "Details: make security-report-code" && exit 1)

security-report-code: ## Detailed code security report
	@echo "Detailed Code Security Report"
	@./scripts/detailed-code-report.sh
	@echo ""
	@echo "Focus on HIGH and CRITICAL findings first"
```

Now when developers encounter a security failure, they can:

1. Run `make security-check` locally to reproduce
2. Run `make security-report-code` to see detailed findings
3. Follow suggested remediation
4. Verify the fix locally before pushing

Security becomes discoverable, repeatable, and teachable.

## Discovering Security Layers

A complete security system reveals itself progressively:

### Container Security Discovery

```makefile
security-containers: ## Show container security commands
	@echo "Container Security"
	@echo "=================="
	@echo "  make security-scan-containers   - Scan for vulnerabilities"
	@echo "  make security-fix-containers    - Suggest fixes"
	@echo "  make security-update-base       - Update base image"

security-scan-containers: ## Scan container for vulnerabilities
	@./scripts/scan-container.sh $(IMAGE_NAME)
	@echo ""
	@echo "Critical issues? Try: make security-fix-containers"

security-fix-containers: ## Suggest container fixes
	@echo "Analyzing vulnerabilities..."
	@./scripts/analyze-container-vulns.sh
	@echo ""
	@echo "Recommended: make security-update-base"
```

### Secret Scanning Discovery

```makefile
security-secrets: ## Show secret scanning commands
	@echo "Secret Scanning"
	@echo "==============="
	@echo "  make security-scan-secrets      - Scan for exposed secrets"
	@echo "  make security-scan-history      - Scan git history"
	@echo "  make security-rotate-secrets    - Rotate exposed secrets"

security-scan-secrets: ## Scan for exposed credentials
	@echo "Scanning for exposed secrets..."
	@./scripts/scan-secrets.sh || \
		echo "Details: make security-secret-details"

security-scan-history: ## Scan git history for secrets
	@echo "Scanning git history..."
	@echo "(This may take a few minutes)"
	@./scripts/scan-git-history.sh
```

### Infrastructure Security Discovery

```makefile
security-infrastructure: ## Show infrastructure security commands
	@echo "Infrastructure Security"
	@echo "======================="
	@echo "  make security-scan-terraform    - Scan Terraform"
	@echo "  make security-scan-k8s          - Scan Kubernetes"
	@echo "  make security-terraform-report  - Detailed findings"

security-scan-terraform: ## Scan Terraform for security issues
	@echo "Scanning Terraform configurations..."
	@./scripts/scan-terraform.sh || \
		echo "Details: make security-terraform-report"
```

Notice the pattern: each area has a menu that reveals available commands, and each command suggests next steps.

## Secret Rotation as Discoverable Workflow

Security isn’t just scanning—it’s operational practices like secret rotation:

```makefile
security-rotate: ## Show secret rotation workflows
	@echo "Secret Rotation Workflows"
	@echo "========================="
	@echo ""
	@echo "Available rotations:"
	@echo "  make rotate-database        - Database passwords"
	@echo "  make rotate-api-keys        - API keys"
	@echo "  make rotate-certificates    - TLS certificates"
	@echo ""
	@echo "Audit: make security-audit-secrets"

rotate-database: ## Rotate database password
	@echo "Rotating database password..."
	@./scripts/rotate-db-password.sh
	@echo "Password rotated"
	@echo "Log it: make audit-log ACTION='rotated db password'"

security-audit-secrets: ## Audit secret age and usage
	@echo "Secret Audit Report"
	@echo "==================="
	@./scripts/audit-secrets.sh
	@echo ""
	@echo "Secrets older than 90 days should be rotated"
```

The workflow is discoverable: `make security-rotate` shows what can be rotated, each rotation is a simple command, and audit trails are built in.

## Compliance as Discoverable Checks

Compliance checks need to be repeatable:

```makefile
compliance-check: ## Run all compliance checks
	@echo "Running compliance checks..."
	@$(MAKE) -s compliance-encryption || exit 1
	@$(MAKE) -s compliance-access || exit 1
	@$(MAKE) -s compliance-logging || exit 1
	@echo "All compliance checks passed"

compliance-encryption: ## Verify encryption requirements
	@echo "Checking encryption compliance..."
	@./scripts/check-encryption.sh

compliance-access: ## Verify access control policies
	@echo "Checking access control..."
	@./scripts/check-access-control.sh

compliance-logging: ## Verify audit logging
	@echo "Checking audit logging..."
	@./scripts/check-audit-logging.sh

compliance-report: ## Generate compliance evidence
	@echo "Generating compliance report..."
	@mkdir -p compliance-reports
	@./scripts/generate-compliance-report.sh
	@echo "Report saved to compliance-reports/"
```

Each check is independently runnable and produces clear pass/fail results.

## Discovering Audit Trails

Maintaining audit trails for compliance:

```makefile
audit-log: ## Log compliance action
	@test -n "$(ACTION)" || \
		(echo "Usage: make audit-log ACTION='description'" && exit 1)
	@echo "$(date -Iseconds) | $(USER) | $(ACTION)" >> audit-trail.log
	@echo "Logged: $(ACTION)"

audit-changes: ## Show infrastructure changes
	@echo "Infrastructure Changes (Last 30 Days)"
	@git log --since="30 days ago" --oneline -- terraform/ k8s/ | head -20

audit-access: ## Show access logs
	@echo "Access Audit Log"
	@./scripts/show-access-logs.sh

audit-package: ## Package audit evidence
	@echo "Packaging audit evidence..."
	@./scripts/package-audit-evidence.sh
	@echo "Audit package created"
```

## Integrating Security into Development

Make security part of the normal workflow:

```makefile
pre-commit: ## Security checks before commit
	@echo "Pre-commit security checks..."
	@$(MAKE) security-scan-secrets
	@$(MAKE) security-scan-code
	@echo "Ready to commit"

pre-push: ## Security checks before push
	@echo "Pre-push security checks..."
	@$(MAKE) security-check
	@echo "Ready to push"

pre-deploy: ## Security validation before deployment
	@echo "Pre-deployment validation..."
	@$(MAKE) security-check
	@$(MAKE) compliance-check
	@$(MAKE) audit-log ACTION="Pre-deployment validation passed"
	@echo "Ready to deploy"

security-quick: ## Quick security scan
	@echo "Quick security scan..."
	@$(MAKE) security-scan-secrets
	@echo "Quick scan complete"
```

Developers can run these locally before the CI pipeline catches issues.

## Real-World Transformation

### Before: Quarterly Compliance Panic

```
Week 1: Compliance team requests evidence

Week 2-3: Engineering scrambles to gather:

  - Screenshots of security scan results
  - Manual exports of audit logs
  - Written attestations about secret rotation

Week 4: Submit evidence, hope it's sufficient

Result: 3 weeks disruption, inconsistent evidence
```

### After: Continuous Compliance Evidence

```makefile
compliance-daily: ## Daily compliance evidence collection
	@echo "Collecting daily compliance evidence..."
	@date_stamp=$(date +%Y%m%d)
	@evidence_dir="compliance-evidence/$$date_stamp"
	@mkdir -p $$evidence_dir
	@$(MAKE) security-check > $$evidence_dir/security.log 2>&1
	@$(MAKE) compliance-check > $$evidence_dir/compliance.log 2>&1
	@./scripts/collect-evidence.sh $$evidence_dir
	@echo "Evidence collected"

compliance-quarterly: ## Package quarterly evidence
	@echo "Packaging quarterly compliance evidence..."
	@./scripts/package-quarterly-evidence.sh
	@echo "Quarterly package ready"
```

Now when auditors request evidence:

```bash
make compliance-quarterly
# Upload to auditor portal
```

Three weeks of scrambling becomes a five-minute task. More importantly, daily evidence collection catches compliance issues **before** the quarterly audit.

## Progressive Security Discovery

Security workflows reveal themselves based on context:

```makefile
security: ## Show security commands for current context
	@if [ -f Dockerfile ]; then \
		echo "Container security:"; \
		echo "  make security-scan-containers"; \
		echo ""; \
	fi
	@if [ -d terraform ]; then \
		echo "Infrastructure security:"; \
		echo "  make security-scan-terraform"; \
		echo ""; \
	fi
	@echo "General security:"; \
	@echo "  make security-check          - Run all scans"
	@echo "  make security-scan-secrets   - Check for exposed secrets"
	@echo "  make security-rotate         - Rotate secrets"
	@echo "  make compliance-check        - Compliance validation"
```

Running `make security` shows only relevant commands for your project structure.

## Key Takeaways

Make-based security and compliance workflows transform these critical responsibilities:

1. **Discoverability**: Security tools become discoverable commands, not hidden pipeline steps
2. **Repeatability**: Run the same checks locally that run in CI
3. **Teachability**: Security failures guide developers toward fixes
4. **Evidence**: Automated collection of compliance evidence
5. **Integration**: Security becomes part of normal workflow

The goal isn’t to replace security teams or automate away human judgment. Instead, Make workflows make security tools accessible to everyone, capture best practices as executable procedures, and generate continuous evidence of compliance.

Most importantly, these workflows transform security from a blocker into a teacher. When a security scan fails, developers don’t just see “scan failed”—they see what failed, why it matters, how to fix it, and how to verify the fix. Security knowledge becomes discoverable team knowledge, captured in version-controlled Make targets that anyone can run, learn from, and improve.

The pattern is consistent: start with `make security` to see what’s available, discover deeper commands as needed, follow the breadcrumbs toward resolution. Security becomes part of the discovery journey rather than a mysterious gate that sometimes blocks your work.

In the next chapter, we’ll explore how to scale these patterns across entire organizations, creating shared Make libraries and standards that work across diverse teams and projects.
