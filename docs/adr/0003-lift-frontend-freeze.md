# Lift the restriction on touching the legacy AngularJS frontend

AGENTS.md previously instructed against upgrading or touching the AngularJS
1.4.9 + jQuery frontend "in passing," citing
`docs/adr/0001-local-only-docker-deploy.md` as the rationale. That citation was
imprecise: ADR 0001 documents a deploy decision (dropping App Engine/Heroku
config for a local-only Dockerfile) and only notes, as an aside, that the
backend's architecture was left unchanged during that pass — it never makes a
decision about the frontend at all.

The actual reason the frontend had stayed untouched was simply that no task
had required otherwise, not a deliberate decision to freeze it. That stopped
holding once we started assigning full-stack coursework (see
`docs/features/sequencias-customizadas/00-enunciado.md`) that explicitly
requires frontend changes.

We're removing the restriction. The frontend remains legacy AngularJS 1.4.9 +
jQuery with no build step, and there's still no plan to modernize the stack
itself — but it's no longer off-limits when a task genuinely needs to touch
it. Modernizing the framework/stack wholesale is a separate, bigger decision
this ADR does not make.
