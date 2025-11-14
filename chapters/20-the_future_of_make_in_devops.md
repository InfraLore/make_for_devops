# Chapter 20 - The Future of Make in DevOps

\chaptersubtitle{Looking ahead at emerging technologies, evolving practices, and
how Make continues to provide value in a changing landscape.}

Make is decades old. In technology terms, that's ancient—older than the personal
computer, older than the internet, older than most programming languages you use
daily. Yet here we are, discussing how this aging tool remains relevant in
modern DevOps practices dominated by containers, cloud platforms, and
AI-assisted development.

This longevity isn't nostalgia or inertia. Make endures because it solves a
problem that keeps recurring: **how do we make complex workflows discoverable
and executable?** Every few years, the specific technologies change—from C
compilation to container builds, from FTP deployments to Kubernetes rollouts—but
the fundamental need remains constant.

As we look toward the future of DevOps, several questions emerge: How will Make
fit into increasingly cloud-native and AI-augmented workflows? What can we learn
from Make's decades of success that applies to whatever tools come next?

This final chapter explores these questions, not to predict the future with
certainty, but to think about how the principles we've learned throughout this
book—discoverability, executable documentation, reducing cognitive load—will
continue to matter regardless of which specific technologies dominate.

## The Unchanging Problems

Before discussing what will change, let's acknowledge what won't:

### The Onboarding Problem

New engineers will always need to learn systems quickly. Whether you're
onboarding to a monolithic application, a microservices architecture, or some
future paradigm we haven't invented yet, the question remains: "How do I build
this? How do I test this? How do I deploy this?"

Executable documentation that answers these questions by doing rather than
describing will always have value.

### The Knowledge Transfer Problem

Teams will always accumulate expertise that needs preservation. Senior engineers
will retire or change roles. Hard-won solutions to production issues will need
capture. Complex workflows will need documentation that stays current.

Tools that make knowledge executable rather than static will always be valuable.

### The Tool Proliferation Problem

Infrastructure will always involve multiple specialized tools. Today it's
Docker, Kubernetes, Terraform, and dozens of others. Tomorrow it will be
different tools, but there will still be many of them, each with its own
interface and learning curve.

Orchestration layers that provide a unified interface across disparate tools
will always be needed.

### The Discoverability Crisis

Projects will always be more complex than any one person can hold in their head.
The "How do I...?" questions will persist. Documentation will drift. Team lore
will accumulate.

Systems that make capabilities discoverable will always matter.

Make addresses these unchanging problems, which is why it has endured and why
the principles behind Make will outlive Make itself.

## Integration with Cloud-Native Technologies

The cloud-native ecosystem continues to evolve rapidly. Make's role in this
ecosystem is evolving too:

### Kubernetes Operators and Custom Resources

As Kubernetes becomes more sophisticated, teams are building custom operators
and resources. Make provides the workflow layer:

```makefile
.PHONY: operator-dev operator-test

operator-dev: ## Start operator development environment
	@kind create cluster --name operator-dev || true
	@kubectl apply -f config/crd/
	@air -c .air.toml

operator-test: ## Test reconciliation loop
	@kubectl apply -f examples/test-resource.yaml
	@sleep 5
	@kubectl get deployment,service -l managed-by=myoperator
```

### Service Mesh Integration

As service meshes become standard, Make workflows adapt:

```makefile
mesh-deploy: ## Deploy with progressive traffic shifting
	@$(MAKE) deploy-canary TRAFFIC=10
	@sleep 300
	@$(MAKE) mesh-check-health && \
		$(MAKE) mesh-shift-traffic TRAFFIC=100 || \
		$(MAKE) mesh-rollback
```

### Platform Engineering and Internal Developer Platforms

Organizations are building Internal Developer Platforms (IDPs). Make serves as
the interface:

```makefile
platform-create-service: ## Create new service from template
	@read -p "Service name: " name; \
	read -p "Team: " team; \
	curl -X POST https://platform.company.com/api/services \
		-d "{\"name\":\"$$name\",\"team\":\"$$team\"}"
	@echo "Service created. Run: cd $$name && make setup"
```

## AI-Augmented Development and the Amplification of Good Practices

AI is changing how we write code and infrastructure, but not in the way many
people initially expected. As Simon Willison articulated in his October 2025
blog post "Vibe Engineering," AI tools don't replace good engineering
practices—they amplify them.\footnote{Simon Willison, "Vibe engineering,"
October 7, 2025, https://simonwillison.net/2025/Oct/7/vibe-engineering/}

Willison observed that AI coding agents work best when they have:

- Automated testing to validate their changes
- Comprehensive documentation to understand the system
- Good version control to track and undo mistakes
- Effective automation already in place
- Clear specifications and success criteria

This is the critical insight: **AI tools amplify existing expertise and
practices rather than replacing them.** The better your engineering
infrastructure, the more productive AI assistance becomes.

This has profound implications for Make-based workflows.

### Make as the Interface for AI Agents

Make provides exactly what AI coding agents need to be effective:

**Discoverability**: An AI agent can run `make help` and immediately understand
what's possible in a codebase. No guessing about build commands, no hunting
through documentation.\footnote{Script delegation pattern---see Chapter 21 for
how this aids learning.}

**Validation loops**: AI agents excel when they can iterate—make a change, test
it, adjust if needed, repeat. Make provides the testing infrastructure:

```makefile
validate: lint test security-check ## Run all validations
	@echo "✓ All validations passed"
```

An AI agent can modify code, run `make validate`, see what failed, and iterate
until everything passes.

**Executable specifications**: Make targets serve as executable specifications
that AI can both read and modify:

```makefile
deploy-production: validate security-scan ## Deploy to production
	@$(MAKE) backup-database
	@$(MAKE) build-and-push
	@kubectl apply -f k8s/production/
	@$(MAKE) smoke-test
```

The AI doesn't need to invent a deployment process—it's right there in the
Makefile.

### Make as Documentation for AI

Here's where Willison's insight becomes most powerful: **comprehensive
documentation is one of the key practices AI tools amplify.**

Make provides multiple layers of documentation that AI can consume:

```makefile
# Layer 1: High-level help
help: ## Show all available commands
	@echo "Common workflows:"
	@echo "  make dev      Start development"
	@echo "  make test     Run tests"
	@echo "  make deploy   Deploy to staging"

# Layer 2: Target-level documentation
deploy-production: validate ## Deploy to production [requires approval]
	# 1. Backup current state
	@$(MAKE) backup-database
	# 2. Build and push new image
	@$(MAKE) build-and-push VERSION=$(VERSION)
	# 3. Update Kubernetes deployment
	@kubectl apply -f k8s/production/
	# 4. Wait for rollout and verify
	@kubectl rollout status deployment/$(APP_NAME)

# Layer 3: Documentation targets
docs-deployment: ## Explain deployment process
	@cat docs/DEPLOYMENT.md
```

An AI agent can query this documentation, understand the system's structure, and
work within established patterns.

### The Amplification Effect

This is where Make's value multiplies in an AI-augmented workflow:

**Before AI agents**: Make reduces cognitive load for human engineers by
providing discoverability and executable documentation.

**With AI agents**: Make provides the same benefits, but now both humans and AI
can leverage them. The human engineer focuses on high-level architecture and
code review. The AI agent handles implementation details, guided by Make's clear
interface.

### Avoiding AI Pitfalls

Willison notes that AI agents "will absolutely cheat if you give them a chance."
Make helps prevent this:

```makefile
deploy-production: check-approvals validate test
	@$(MAKE) _do-deploy

# Private target - signals "don't call directly"
_do-deploy:
	@[ -n "$(APPROVED)" ] || (echo "Use: make deploy-production" && exit 1)
	@echo "Deploying..."
```

The dependency chain enforces proper workflow ordering. AI agents must go
through the front door.

### What This Means for Make's Future

AI tools don't threaten Make's relevance—they enhance it. As AI agents become
more capable at writing code, the human engineer's role shifts toward:

- Defining high-level architecture
- Writing specifications (which Make targets are)
- Code review (which Make's dry-run makes easier)
- Maintaining test suites (which Make executes)

All of these are things Make already supports well.

The pattern Willison describes as "vibe engineering"—seasoned professionals
using AI to accelerate their work while remaining accountable—is exactly the
pattern Make enables. The Makefile is the contract: it specifies what should
happen, AI helps implement it, humans verify the result.

## Observability and OpenTelemetry

As observability standards mature, Make workflows integrate deeper:

```makefile
otel-trace-deployment: ## Trace deployment with OpenTelemetry
	@trace_id=$$(uuidgen)
	@echo "View trace: https://jaeger.company.com/trace/$$trace_id"
	@OTEL_TRACE_ID=$$trace_id $(MAKE) build
	@OTEL_TRACE_ID=$$trace_id $(MAKE) test
	@OTEL_TRACE_ID=$$trace_id $(MAKE) deploy
```

## FinOps and Cost Optimization

As cloud costs become more important, Make helps with cost awareness:

```makefile
cost-estimate: ## Estimate deployment costs
	@infracost breakdown --path terraform/ > cost.json
	@monthly=$$(jq -r '.totalMonthlyCost' cost.json)
	@echo "Estimated monthly: \$$$$monthly"
	@[ "$$(echo "$$monthly > 10000" | bc)" -eq 0 ] || \
		(echo "High cost! Approve? [y/N]" && read ans && [ "$$ans" = "y" ])
```

## Security Evolution

Security practices continue to mature:

### Supply Chain Security

```makefile
sbom-generate: ## Generate Software Bill of Materials
	@syft packages dir:. -o spdx-json > sbom.json

sign-artifacts: ## Sign release artifacts with Sigstore
	@cosign sign $(IMAGE_NAME):$(VERSION)
	@cosign sign-blob sbom.json --output-signature sbom.json.sig
```

### Zero Trust Architecture

```makefile
ztrust-deploy: ## Deploy with zero trust verification
	@$(MAKE) _verify-identity
	@$(MAKE) _verify-image-provenance
	@$(MAKE) _verify-policy
	@$(MAKE) deploy

_verify-image-provenance:
	@cosign verify --policy policy.yaml $(IMAGE_NAME):$(VERSION)
```

## The Evolution of Make Itself

Make isn't static. While GNU Make remains stable, the ecosystem evolves:

### Modern Make Alternatives

Tools inspired by Make but designed for modern workflows emerge:

- **Just**: Modern command runner with better syntax
- **Task**: Go-based alternative with YAML configuration
- **Earthly**: Make meets Dockerfile
- **Mage**: Make in Go

These tools address some of Make's limitations while preserving core principles.
The key insight: **the problem Make solves endures, even if better solutions
emerge**.

## Career Development and Skill Building

Understanding Make-based workflows becomes a valuable skill:

### The DevOps Engineer's Toolkit

Modern DevOps engineers benefit from understanding:

1. **Workflow Orchestration**: How to coordinate multiple tools
2. **Discoverability Patterns**: Making complex systems approachable
3. **Documentation as Code**: Keeping docs and reality synchronized
4. **Team Knowledge Capture**: Preserving expertise systematically

Make teaches these principles in a practical, hands-on way.

### Building a Culture of Executable Documentation

The most important legacy isn't Make itself—it's the cultural shift toward
executable documentation:

```makefile
# Cultural patterns that transcend any specific tool

help:              # 1. Discoverability First
quick-start:       # 2. Progressive Disclosure
target: ##         # 3. Self-Documenting
deploy: validate   # 4. Validation Built In
incident-response: # 5. Team Knowledge Captured
```

## What Comes After Make?

Eventually, something will replace Make. What will that look like?

### Desired Characteristics

The ideal DevOps workflow tool would combine:

- **Make's discoverability**: `make help` shows what's possible
- **Make's simplicity**: Text files, no compilation, version-controlled
- **Make's universality**: Available everywhere, no installation friction
- **Better syntax**: More intuitive than Make's quirks
- **Better parallelism**: Smarter about concurrent execution
- **Better error handling**: Clearer failure modes and debugging
- **Native cloud integration**: First-class support for cloud platforms

### What Won't Change

Regardless of the tool:

- **Workflows need coordination**: Multiple steps, multiple tools
- **Teams need discoverability**: How do I X? What can I do?
- **Documentation must stay current**: Executable > static
- **Knowledge must be preserved**: Team lore needs capture
- **Complexity must be manageable**: Progressive disclosure matters

The principles we've explored—executable documentation, discoverability,
reducing cognitive load—will remain valuable regardless of which specific tools
implement them.

## Practical Next Steps

So where do you go from here? Some suggestions:

### For Individual Engineers

1. **Start small**: Add a Makefile with `help`, `test`, `build`, `deploy`
2. **Iterate**: Add targets as you discover repetitive tasks
3. **Share knowledge**: Turn "How do I...?" questions into Make targets
4. **Practice debugging**: Use the techniques from Chapter 19
5. **Teach others**: Help teammates adopt executable documentation

### For Teams

1. **Establish conventions**: Agree on standard target names
2. **Build libraries**: Create shared Make code for common patterns
3. **Template projects**: Provide good starting points
4. **Measure impact**: Track onboarding time, MTTR, deployment frequency
5. **Evolve continuously**: Make is a framework, not a destination

### For Organizations

1. **Create platform standards**: Shared libraries across teams
2. **Invest in tooling**: Support Make-based workflows
3. **Train engineers**: Make discoverability a valued skill
4. **Build culture**: Encourage executable documentation
5. **Measure success**: Correlate Make adoption with business metrics

## Final Thoughts

Make's decades-long history teaches us something profound: **good solutions to
fundamental problems endure**. The specific technologies change—we're not
compiling C programs anymore—but the underlying need for discoverable,
executable workflows remains constant.

This book has been about more than Make. It's been about:

- **Reducing cognitive load** in complex systems
- **Preserving team knowledge** in executable form
- **Making expertise accessible** to all team members
- **Creating systems that teach** while they execute
- **Building workflows that scale** across teams and time

Make is one implementation of these principles. It's a good one, battle-tested
and proven. But the principles transcend Make. Whether you use Make, or Task, or
Just, or something not yet invented, the goal remains: **make your workflows
discoverable, executable, and improvable**.

The future of DevOps won't be determined by which orchestration tool wins, but
by how well we solve the human problems—onboarding, knowledge transfer,
discoverability, collaboration—that persist regardless of technology.

Make has taught us valuable lessons. Now it's up to us to apply them, whether
we're using Make itself or building the tools that come after.

The workflows you document today become the institutional knowledge that
empowers your team tomorrow. Make them discoverable. Make them executable. Make
them better.

---

*"The real problem is not whether machines think but whether men do."* — B.F.
Skinner

Perhaps we should ask: not whether our tools are perfect, but whether they help
us think clearly about our work, share knowledge effectively, and build systems
that last.

That's the real legacy of Make, and that's the future worth building.

# From Organization to Individual

We've spent this chapter thinking about Make at scale: how it fits into cloud
platforms, how it interfaces with AI agents, how organizations build cultures
around executable documentation. These are important questions about Make's role
in the broader DevOps landscape.

But before we conclude, let's zoom back in from the organizational to the
personal.

All the principles we've discussed—discoverability, executable documentation,
reducing cognitive load—apply just as powerfully to individual learning as they
do to team workflows. In fact, they might matter even more for the solo engineer
trying to master an overwhelming ecosystem of tools.

The next chapter shifts perspective entirely. We're going to explore Make not as
a team coordination tool, but as a personal learning system. How do you capture
knowledge as you acquire it? How do you make your hard-won solutions findable
when you need them again? How do you build expertise incrementally without
drowning in complexity?

The same tool that helps teams onboard new engineers can help you onboard
yourself to new technologies. The same patterns that make organizational
knowledge accessible can make your own accumulated learning navigable.

Let's explore how Make becomes your personal reference manual—one that executes
rather than merely describes.
