# Chapter 17 - Security and Compliance Workflows

\chaptersubtitle{Making security scanners discoverable, compliance checks repeatable, and audit trails automatic.}

Your company just landed a major enterprise client, but there's a catch: they require SOC 2 Type II compliance, quarterly security audits, and evidence that you're running vulnerability scans before every deployment. The security team sends you a 47-page compliance checklist. You now need to prove that you scan container images, rotate secrets monthly, validate TLS certificates, check for exposed credentials in code, maintain audit logs, and document all configuration changes.

You look at your deployment pipeline. It works—containers build, tests pass, deployments succeed. But security scanning? That's a manual step someone runs "when they remember." Secret rotation happens "sometime" using a process that's different for each service. Audit logs exist somewhere, but nobody's sure how to query them. The compliance checklist might as well be written in ancient Greek.

The security team's recommendation: "Add security scanning tools to your pipeline." This sounds simple until you discover there are dozens of tools—Trivy, Snyk, Grype, Clair for containers; TruffleHog, git-secrets, GitLeaks for credential scanning; tfsec, Checkov for infrastructure; gosec, bandit, semgrep for code. Each has different installation procedures, configuration files, output formats, and failure criteria. Your simple deployment pipeline is about to become a maze of security tools that nobody understands.

This is where most teams make a critical mistake: they add the tools but don't make them **discoverable or repeatable**. Security scanning becomes something that "happens in CI" but nobody knows how to run locally, interpret results, or fix issues. Compliance checks happen quarterly when auditors ask, requiring frantic scrambling to gather evidence.

Make offers a better approach: **security and compliance as discoverable workflows**. Instead of hidden pipeline steps, create explicit targets that developers can run, understand, and improve.

## The Problem with Hidden Security

Traditional security integration follows a pattern: the security team mandates a tool, someone adds it to the CI pipeline, and it becomes an invisible step that either passes (good!) or fails (mysterious!). Developers encounter security failures like this:

```
❌ Build failed: Security scan detected vulnerabilities
See: https://ci.company.com/build/12847/security-scan
```

They click the link, see a wall of JSON output, and... now what? Which vulnerabilities are critical? How do they fix them? Can they test the fix locally? Is there a way to temporarily bypass non-critical issues? The security tool has become a blocker without being a teacher.

Here's the same security check as a discoverable Make target:

```makefile
.PHONY: security-check security-scan-containers security-scan-code

security-check: ## Run all security scans
	@echo "🔒 Running security checks..."
	@echo ""
	@$(MAKE) security-scan-containers && echo "✅ Container scan passed" || \
		(echo "❌ Container scan failed" && exit 1)
	@$(MAKE) security-scan-code && echo "✅ Code scan passed" || \
		(echo "❌ Code scan failed" && exit 1)
	@$(MAKE) security-scan-secrets && echo "✅ Secret scan passed" || \
		(echo "❌ Secret scan failed" && exit 1)
	@echo ""
	@echo "✅ All security checks passed!"

security-scan-containers: ## Scan container images for vulnerabilities
	@echo "🔍 Scanning container images..."
	@if ! command -v trivy >/dev/null; then \
		echo "Installing trivy..."; \
		$(MAKE) _install-trivy; \
	fi
	@trivy image --severity HIGH,CRITICAL \
		--exit-code 1 \
		$(IMAGE_NAME):$(VERSION) || \
		(echo ""; \
		 echo "💡 To see full report: make security-report-containers"; \
		 echo "💡 To fix: update base image or patch vulnerabilities"; \
		 exit 1)

security-scan-code: ## Scan code for security issues
	@echo "🔍 Scanning code for vulnerabilities..."
	@if ! command -v semgrep >/dev/null; then \
		echo "Installing semgrep..."; \
		pip install semgrep --quiet; \
	fi
	@semgrep --config=auto --error --quiet . || \
		(echo ""; \
		 echo "💡 To see details: make security-report-code"; \
		 echo "💡 To fix: address findings in semgrep output"; \
		 exit 1)

security-report-containers: ## Detailed container vulnerability report
	@echo "📋 Detailed Container Vulnerability Report"
	@echo "========================================="
	@trivy image --format table $(IMAGE_NAME):$(VERSION)
	@echo ""
	@echo "💡 Focus on HIGH and CRITICAL vulnerabilities first"
	@echo "💡 Run 'make security-fix-container' for common fixes"
```

Now when developers encounter a security failure, they can:
1. Run `make security-check` locally to reproduce the issue
2. Run `make security-report-containers` to see detailed findings
3. Follow suggested remediation steps
4. Verify the fix locally before pushing

Security becomes discoverable, repeatable, and teachable.

## Building a Comprehensive Security Scanning System

A complete security scanning system typically includes multiple layers:

### Layer 1: Container Security

```makefile
# Container image security scanning
.PHONY: security-container-scan security-container-fix

security-container-scan: ## Scan container for vulnerabilities
	@echo "🔍 Scanning $(IMAGE_NAME):$(VERSION)..."
	@trivy image \
		--severity HIGH,CRITICAL \
		--format json \
		--output trivy-report.json \
		$(IMAGE_NAME):$(VERSION)
	@critical=$$(jq '[.Results[].Vulnerabilities[]? | \
		select(.Severity=="CRITICAL")] | length' trivy-report.json); \
	high=$$(jq '[.Results[].Vulnerabilities[]? | \
		select(.Severity=="HIGH")] | length' trivy-report.json); \
	echo ""; \
	echo "Found: $$critical CRITICAL, $$high HIGH vulnerabilities"; \
	if [ $$critical -gt 0 ]; then \
		echo "❌ CRITICAL vulnerabilities must be fixed"; \
		exit 1; \
	fi

security-container-fix: ## Suggest fixes for container vulnerabilities
	@echo "🔧 Analyzing vulnerabilities..."
	@echo ""
	@echo "Base image vulnerabilities:"
	@jq -r '.Results[] | select(.Target | contains("alpine")) | 
		.Vulnerabilities[]? | 
		select(.Severity=="CRITICAL" or .Severity=="HIGH") |
		"  - \(.VulnerabilityID): \(.PkgName) \(.InstalledVersion) -> \
		\(.FixedVersion // "no fix available")"' trivy-report.json | \
		head -10
	@echo ""
	@echo "💡 Recommended actions:"
	@echo "   1. Update base image to latest version"
	@echo "   2. Run: make security-update-base-image"
	@echo "   3. If issues persist, check: make security-container-detail"

security-update-base-image: ## Update Dockerfile base image
	@echo "Updating base image in Dockerfile..."
	@current=$$(grep "^FROM" Dockerfile | head -1 | awk '{print $$2}'); \
	echo "Current base image: $$current"; \
	# Script would update to latest version
	@echo "💡 Manual step: Update FROM line in Dockerfile to latest tag"
	@echo "💡 Then rebuild: make build"
```

### Layer 2: Secret Scanning

```makefile
# Credential and secret scanning
.PHONY: security-scan-secrets security-scan-history

security-scan-secrets: ## Scan for exposed secrets
	@echo "🔍 Scanning for exposed credentials..."
	@if ! command -v trufflehog >/dev/null; then \
		echo "Installing trufflehog..."; \
		$(MAKE) _install-trufflehog; \
	fi
	@trufflehog filesystem . \
		--json \
		--no-update \
		2>/dev/null | \
		jq -r 'select(.Verified==true) | 
		"❌ VERIFIED SECRET: \(.SourceMetadata.Data.Filesystem.file)"' | \
		if grep -q "VERIFIED SECRET"; then \
			echo ""; \
			echo "❌ Verified secrets found!"; \
			echo "💡 Run: make security-secret-detail"; \
			exit 1; \
		else \
			echo "✅ No verified secrets detected"; \
		fi

security-scan-history: ## Scan git history for secrets
	@echo "🔍 Scanning git history for credentials..."
	@echo "(This may take a few minutes for large repositories)"
	@trufflehog git file://. \
		--since-commit HEAD~100 \
		--only-verified \
		--json 2>/dev/null | \
		jq -r 'select(.Verified==true) | 
		"Found in: \(.SourceMetadata.Data.Git.commit) - \
		\(.SourceMetadata.Data.Git.file)"' | \
		if [ -s /dev/stdin ]; then \
			echo "⚠️  Secrets found in git history"; \
			echo "💡 These need rotation even if removed from current code"; \
			echo "💡 Run: make security-rotate-exposed-secrets"; \
		else \
			echo "✅ No secrets in recent history"; \
		fi

security-secret-detail: ## Show detailed secret scan results
	@echo "📋 Detailed Secret Scan Report"
	@echo "============================="
	@trufflehog filesystem . --json --no-update 2>/dev/null | \
		jq -r 'select(.Verified==true) | 
		"\n🔴 \(.DetectorName) credential found:\n   File: \
		\(.SourceMetadata.Data.Filesystem.file)\n   Line: \
		\(.SourceMetadata.Data.Filesystem.line)"' | \
		head -20
	@echo ""
	@echo "💡 Next steps:"
	@echo "   1. Rotate all exposed credentials immediately"
	@echo "   2. Move secrets to secure storage (AWS Secrets Manager, etc)"
	@echo "   3. Update code to fetch from secure storage"
	@echo "   4. Run: make security-setup-secret-management"
```

### Layer 3: Infrastructure Security

```makefile
# Infrastructure as Code security scanning
.PHONY: security-scan-terraform security-scan-k8s

security-scan-terraform: ## Scan Terraform for security issues
	@echo "🔍 Scanning Terraform configurations..."
	@if ! command -v tfsec >/dev/null; then \
		echo "Installing tfsec..."; \
		$(MAKE) _install-tfsec; \
	fi
	@tfsec terraform/ \
		--format json \
		--out tfsec-report.json \
		--soft-fail
	@critical=$$(jq '[.results[] | select(.severity=="CRITICAL")] | \
		length' tfsec-report.json); \
	high=$$(jq '[.results[] | select(.severity=="HIGH")] | \
		length' tfsec-report.json); \
	echo "Found: $$critical CRITICAL, $$high HIGH issues"; \
	if [ $$critical -gt 0 ]; then \
		echo "❌ CRITICAL issues must be fixed"; \
		echo "💡 Details: make security-terraform-report"; \
		exit 1; \
	fi

security-scan-k8s: ## Scan Kubernetes manifests
	@echo "🔍 Scanning Kubernetes configurations..."
	@if ! command -v kubesec >/dev/null; then \
		echo "Installing kubesec..."; \
		$(MAKE) _install-kubesec; \
	fi
	@for file in k8s/*.yaml; do \
		echo "Checking $$file..."; \
		kubesec scan $$file | \
			jq -r 'if .score < 0 then 
			"❌ \(.object): Score \(.score) - Security issues found" 
			else "✅ \(.object): Score \(.score)" end'; \
	done

security-terraform-report: ## Detailed Terraform security report
	@echo "📋 Terraform Security Report"
	@echo "============================"
	@jq -r '.results[] | select(.severity=="CRITICAL" or \
		.severity=="HIGH") | 
		"\n[\(.severity)] \(.rule_description)\n  File: \(.location.filename):\
		\(.location.start_line)\n  Impact: \(.impact)\n  Fix: \
		\(.resolution)"' tfsec-report.json
	@echo ""
	@echo "💡 Fix critical issues, then run: make security-scan-terraform"
```

### Layer 4: Dependency Security

```makefile
# Dependency vulnerability scanning
.PHONY: security-scan-deps security-update-deps

security-scan-deps: ## Scan dependencies for vulnerabilities
	@echo "🔍 Scanning dependencies..."
	@if [ -f package.json ]; then \
		echo "Checking npm dependencies..."; \
		npm audit --audit-level=high --json > npm-audit.json || true; \
		critical=$$(jq '.metadata.vulnerabilities.critical' npm-audit.json); \
		high=$$(jq '.metadata.vulnerabilities.high' npm-audit.json); \
		echo "npm: $$critical CRITICAL, $$high HIGH vulnerabilities"; \
		if [ $$critical -gt 0 ]; then \
			echo "💡 Fix: make security-update-deps"; \
		fi; \
	fi
	@if [ -f requirements.txt ]; then \
		echo "Checking Python dependencies..."; \
		pip-audit --format json > pip-audit.json || true; \
		vulns=$$(jq '[.vulnerabilities[]] | length' pip-audit.json); \
		echo "pip: $$vulns vulnerabilities found"; \
	fi

security-update-deps: ## Update dependencies to fix vulnerabilities
	@echo "🔧 Updating dependencies..."
	@if [ -f package.json ]; then \
		echo "Updating npm dependencies..."; \
		npm audit fix || npm audit fix --force; \
		echo "✅ npm dependencies updated"; \
	fi
	@if [ -f requirements.txt ]; then \
		echo "Updating Python dependencies..."; \
		pip-audit --fix || echo "⚠️  Manual fixes required"; \
		echo "💡 Review changes and test before committing"; \
	fi
	@echo ""
	@echo "Verify: make test && make security-scan-deps"
```

## Secret Rotation and Management

Security isn't just about scanning—it's about operational practices like regular secret rotation:

```makefile
# Secret rotation workflows
.PHONY: security-rotate-secrets security-rotate-db security-audit-secrets

security-rotate-secrets: ## Rotate all secrets (interactive)
	@echo "🔄 Secret Rotation Workflow"
	@echo "=========================="
	@echo ""
	@echo "Secrets to rotate:"
	@echo "  1. Database passwords"
	@echo "  2. API keys"
	@echo "  3. TLS certificates"
	@echo "  4. Service account tokens"
	@echo ""
	@echo "This is a guided process. Each step will:"
	@echo "  - Generate new credentials"
	@echo "  - Update secret storage"
	@echo "  - Verify services still work"
	@echo "  - Retire old credentials"
	@echo ""
	@echo "Start with: make security-rotate-db"

security-rotate-db: ## Rotate database password
	@echo "🔄 Rotating database password..."
	@echo ""
	@echo "Current password expires: $$(date -d '+30 days' +%Y-%m-%d)"
	@new_password=$$(openssl rand -base64 32); \
	echo "1. Generated new password"; \
	echo "2. Updating AWS Secrets Manager..."; \
	aws secretsmanager update-secret \
		--secret-id prod/db/password \
		--secret-string "$$new_password" \
		--description "Rotated on $$(date)" >/dev/null; \
	echo "3. Restarting services to pick up new password..."; \
	kubectl rollout restart -n production deploy/api; \
	echo "4. Waiting for services to be healthy..."; \
	kubectl rollout status -n production deploy/api; \
	echo ""; \
	echo "✅ Database password rotated successfully"; \
	echo "💡 Record rotation in: make security-audit-log"

security-rotate-api-keys: ## Rotate external API keys
	@echo "🔄 Rotating API keys..."
	@echo ""
	@echo "API keys to rotate:"
	@aws secretsmanager list-secrets \
		--filters Key=name,Values=prod/api-key \
		--query 'SecretList[].Name' \
		--output text | \
		tr '\t' '\n' | \
		while read secret; do \
			age=$$(aws secretsmanager describe-secret --secret-id $$secret \
				--query 'LastRotatedDate' --output text); \
			echo "  - $$secret (last rotated: $$age)"; \
		done
	@echo ""
	@echo "💡 Rotate individual keys with:"
	@echo "   make security-rotate-key KEY=prod/api-key/service-name"

security-audit-secrets: ## Audit secret age and usage
	@echo "📋 Secret Audit Report"
	@echo "====================="
	@echo ""
	@echo "Secrets older than 90 days:"
	@aws secretsmanager list-secrets \
		--query "SecretList[?LastRotatedDate<='$$(date -d '90 days ago' \
		--iso-8601)'].{Name:Name,Age:LastRotatedDate}" \
		--output table
	@echo ""
	@echo "⚠️  These secrets should be rotated soon"
	@echo "💡 Use: make security-rotate-secrets"
```

## Compliance Validation and Reporting

Compliance checks need to be repeatable and auditable:

```makefile
# Compliance checking workflows
.PHONY: compliance-check compliance-soc2 compliance-report

compliance-check: ## Run all compliance checks
	@echo "📋 Running compliance checks..."
	@echo ""
	@$(MAKE) compliance-encryption && echo "✅ Encryption: Compliant" || \
		echo "❌ Encryption: Issues found"
	@$(MAKE) compliance-access-control && \
		echo "✅ Access Control: Compliant" || \
		echo "❌ Access Control: Issues found"
	@$(MAKE) compliance-audit-logging && \
		echo "✅ Audit Logging: Compliant" || \
		echo "❌ Audit Logging: Issues found"
	@$(MAKE) compliance-backup && echo "✅ Backups: Compliant" || \
		echo "❌ Backups: Issues found"

compliance-encryption: ## Verify encryption requirements
	@echo "🔍 Checking encryption compliance..."
	@# Check EBS encryption
	@unencrypted=$$(aws ec2 describe-volumes \
		--filters Name=encrypted,Values=false \
		--query 'Volumes[].VolumeId' \
		--output text | wc -w); \
	if [ $$unencrypted -gt 0 ]; then \
		echo "❌ Found $$unencrypted unencrypted volumes"; \
		exit 1; \
	fi
	@# Check S3 encryption
	@aws s3api list-buckets --query 'Buckets[].Name' --output text | \
		tr '\t' '\n' | while read bucket; do \
		encryption=$$(aws s3api get-bucket-encryption --bucket $$bucket \
			2>/dev/null || echo "none"); \
		if [ "$$encryption" = "none" ]; then \
			echo "❌ Bucket $$bucket: encryption not enabled"; \
			exit 1; \
		fi; \
	done
	@echo "✅ All storage encrypted"

compliance-access-control: ## Verify access control policies
	@echo "🔍 Checking access control compliance..."
	@# Check for overly permissive IAM policies
	@overly_permissive=$$(aws iam list-policies \
		--scope Local \
		--query 'Policies[].PolicyName' \
		--output text | \
		xargs -I {} aws iam get-policy-version \
		--policy-arn {} \
		--version-id v1 \
		--query 'PolicyVersion.Document' | \
		grep -c '"Effect":"Allow","Action":"\*"' || echo "0"); \
	if [ $$overly_permissive -gt 0 ]; then \
		echo "⚠️  Found policies with overly broad permissions"; \
		echo "💡 Review: make compliance-access-report"; \
	else \
		echo "✅ No overly permissive policies found"; \
	fi

compliance-audit-logging: ## Verify audit logging is enabled
	@echo "🔍 Checking audit logging compliance..."
	@# Check CloudTrail
	@trails=$$(aws cloudtrail describe-trails \
		--query 'trailList[?IsMultiRegionTrail==`true`]' | \
		jq length); \
	if [ $$trails -eq 0 ]; then \
		echo "❌ No multi-region CloudTrail enabled"; \
		exit 1; \
	fi
	@# Check application audit logs
	@if kubectl get configmap -n production audit-config >/dev/null 2>&1; \
	then \
		echo "✅ Application audit logging configured"; \
	else \
		echo "❌ Application audit logging not configured"; \
		exit 1; \
	fi

compliance-report: ## Generate compliance evidence report
	@echo "📋 Generating compliance report..."
	@mkdir -p compliance-reports
	@report="compliance-reports/report-$$(date +%Y%m%d).md"
	@echo "# Compliance Report - $$(date)" > $$report
	@echo "" >> $$report
	@echo "## Encryption Compliance" >> $$report
	@$(MAKE) compliance-encryption >> $$report 2>&1 || true
	@echo "" >> $$report
	@echo "## Access Control Compliance" >> $$report
	@$(MAKE) compliance-access-control >> $$report 2>&1 || true
	@echo "" >> $$report
	@echo "## Audit Logging Compliance" >> $$report
	@$(MAKE) compliance-audit-logging >> $$report 2>&1 || true
	@echo "" >> $$report
	@echo "## Security Scan Results" >> $$report
	@$(MAKE) security-check >> $$report 2>&1 || true
	@echo ""
	@echo "✅ Report saved to $$report"
```

## Audit Trail Generation

Maintaining audit trails for compliance:

```makefile
# Audit trail and evidence collection
.PHONY: audit-log audit-changes audit-access audit-package

audit-log: ## Log compliance action
	@if [ -z "$(ACTION)" ]; then \
		echo "Usage: make audit-log ACTION='description'"; \
		exit 1; \
	fi
	@echo "$$(date -Iseconds) | $(USER) | $(ACTION)" >> \
		audit-trail.log
	@echo "✅ Logged: $(ACTION)"

audit-changes: ## Show infrastructure changes (last 30 days)
	@echo "📋 Infrastructure Changes (Last 30 Days)"
	@echo "========================================"
	@git log --since="30 days ago" \
		--pretty=format:"%h | %ad | %an | %s" \
		--date=short \
		-- terraform/ k8s/ | \
		head -20
	@echo ""
	@echo "💡 Full details: git log --since='30 days ago' -- terraform/ k8s/"

audit-access: ## Show access logs for security review
	@echo "📋 Access Audit Log"
	@echo "=================="
	@echo ""
	@echo "Recent kubectl access:"
	@kubectl logs -n kube-system deploy/kube-apiserver \
		--since=24h | \
		grep "user=" | \
		awk '{print $1, $2, $NF}' | \
		sort -u | \
		tail -20
	@echo ""
	@echo "Recent AWS API calls:"
	@aws cloudtrail lookup-events \
		--lookup-attributes AttributeKey=EventName,AttributeValue=AssumeRole \
		--max-results 10 \
		--query 'Events[].{Time:EventTime,User:Username,Event:EventName}' \
		--output table

audit-package: ## Package audit evidence for review
	@echo "📦 Packaging audit evidence..."
	@timestamp=$$(date +%Y%m%d_%H%M%S)
	@audit_dir="audit-package-$$timestamp"
	@mkdir -p $$audit_dir
	@$(MAKE) compliance-report
	@cp compliance-reports/report-*.md $$audit_dir/
	@$(MAKE) audit-changes > $$audit_dir/infrastructure-changes.txt
	@cp audit-trail.log $$audit_dir/
	@git log --since="90 days ago" --pretty=format:"%h | %ad | %an | %s" \
		--date=short > $$audit_dir/git-history.txt
	@tar czf $$audit_dir.tar.gz $$audit_dir
	@echo "✅ Audit package created: $$audit_dir.tar.gz"
```

## Integrating Security into Development Workflow

The key to successful security integration is making it part of the normal development workflow:

```makefile
# Pre-commit security checks
.PHONY: pre-commit security-quick

pre-commit: ## Run quick security checks before commit
	@echo "🔍 Pre-commit security checks..."
	@$(MAKE) security-scan-secrets
	@$(MAKE) security-scan-code
	@echo "✅ Ready to commit"

# Pre-push security checks  
pre-push: ## Run security checks before push
	@echo "🔍 Pre-push security checks..."
	@$(MAKE) security-check
	@echo "✅ Ready to push"

# Pre-deploy security validation
pre-deploy: ## Security validation before deployment
	@echo "🔍 Pre-deployment security validation..."
	@$(MAKE) security-check
	@$(MAKE) compliance-check
	@$(MAKE) audit-log ACTION="Pre-deployment validation passed"
	@echo "✅ Ready to deploy"

security-quick: ## Quick security scan (fast, for frequent use)
	@echo "⚡ Quick security scan..."
	@$(MAKE) security-scan-secrets
	@if git diff --cached --name-only | grep -q "\.tf$$"; then \
		$(MAKE) security-scan-terraform; \
	fi
	@echo "✅ Quick scan complete"
```

## Real-World Example: From Compliance Chaos to Automated Evidence

Let's look at a transformation from manual compliance checking to automated evidence collection:

### Before: Quarterly Compliance Panic

```
Week 1 of Quarter: Compliance team requests evidence
Week 2-3: Engineering scrambles to gather:
  - Screenshots of security scan results
  - Manual exports of audit logs  
  - Written attestations about secret rotation
  - Spot-checks of encryption settings
Week 4: Submit evidence, hope it's sufficient
Result: 3 weeks of disruption, inconsistent evidence, manual errors
```

### After: Continuous Compliance Evidence

```makefile
# Automated compliance evidence collection (runs daily in CI)
compliance-daily: ## Daily compliance evidence collection
	@echo "📋 Collecting daily compliance evidence..."
	@date_stamp=$$(date +%Y%m%d)
	@evidence_dir="compliance-evidence/$$date_stamp"
	@mkdir -p $$evidence_dir
	
	@# Security scan evidence
	@$(MAKE) security-check > $$evidence_dir/security-scans.log 2>&1 || \
		echo "Security issues found" > $$evidence_dir/security-issues.flag
	
	@# Encryption compliance
	@$(MAKE) compliance-encryption > $$evidence_dir/encryption.log 2>&1
	
	@# Access control audit
	@$(MAKE) audit-access > $$evidence_dir/access-audit.log 2>&1
	
	@# Secret rotation status
	@$(MAKE) security-audit-secrets > $$evidence_dir/secret-audit.log 2>&1
	
	@# Configuration snapshot
	@kubectl get configmaps,secrets -n production \
		-o name > $$evidence_dir/config-inventory.txt
	
	@echo "✅ Evidence collected: $$evidence_dir"
	@$(MAKE) audit-log ACTION="Daily compliance evidence collected"

# Quarterly compliance package (just bundles daily evidence)
compliance-quarterly: ## Package quarterly compliance evidence
	@echo "📦 Packaging quarterly compliance evidence..."
	@quarter=$$(date +%Y-Q%q)
	@tar czf compliance-$$quarter.tar.gz compliance-evidence/
	@echo "✅ Created compliance-$$quarter.tar.gz"
	@echo ""
	@echo "Evidence includes:"
	@echo "  - Daily security scan results"
	@echo "  - Encryption compliance checks"
	@echo "  - Access audit logs"
	@echo "  - Secret rotation history"
	@echo "  - Configuration inventories"
```

Now when auditors request evidence:

```bash
# Generate quarterly package
make compliance-quarterly

# Upload to auditor portal
aws s3 cp compliance-2025-Q1.tar.gz s3://audit-evidence/
```

Three weeks of scrambling becomes a five-minute task. More importantly, the daily evidence collection catches compliance issues **before** the quarterly audit, not during it.

## Key Takeaways

Make-based security and compliance workflows transform how teams handle these critical but often-dreaded responsibilities:

1. **Discoverability**: Security tools become discoverable commands, not hidden pipeline steps
2. **Repeatability**: Run the same checks locally that run in CI
3. **Teachability**: Security failures guide developers toward fixes
4. **Evidence**: Automated collection of compliance evidence
5. **Integration**: Security becomes part of normal workflow, not a bolt-on afterthought

The goal isn't to replace security teams or automate away human judgment. Instead, Make-based workflows make security tools accessible to everyone, capture best practices as executable procedures, and generate continuous evidence of compliance.

Most importantly, these workflows transform security from a blocker into a teacher. When a security scan fails, developers don't just see "scan failed"—they see what failed, why it matters, how to fix it, and how to verify the fix. Security knowledge that used to live only in the security team's expertise becomes discoverable team lore, captured in version-controlled Make targets that anyone can run, learn from, and improve.

In the next chapter, we'll explore how to scale these patterns across entire organizations, creating shared Make libraries and standards that work across diverse teams and projects.