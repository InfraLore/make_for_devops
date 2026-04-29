# Foreword

This book starts with a demo I couldn't stop thinking about.

In 2017, at Samvera Connect in Evanston, Illinois, I proposed an unconference
session on developer workspaces. My motivation was simple and a little
desperate: at the time, getting a Samvera development environment running was a
steep, lore-driven affair, the kind of thing where you needed a senior engineer
looking over your shoulder for most of a day. I wanted to show off what Vagrant
could do, and hopefully find some collaborators to build something better.

What I didn't expect was John H. Robinson IV.

John sat down and proceeded to ad-lib an entire development environment on the
spot. He called a Make target. Then another. Vagrant spun up whatever he
needed-- a database, a web server, a job queue--pulling pieces from past
projects, assembling them into something new. He wasn't following a script. He
was composing. In minutes, he was working. I was blown away.

I asked him for the Makefile afterward. He shared it -- you can still find it at
[vagrant-as-infrastructure](https://github.com/jhriv/vagrant-as-infrastructure)[^vagrant]
-- and its README states the philosophy plainly: "Makefile is all you need.
Everything else can be downloaded automatically." I poked at it, found it deeply
weird, and set it aside.

Then, gradually, I started noticing Makefiles everywhere. In projects I admired.
In tools I used daily. Node.js itself is built with one. The humble Makefile, it
turns out, never went anywhere: I just hadn't been paying attention.

I knew someone should write a book about Make for DevOps. I went looking.
Nothing. Blog posts, conference talks, scattered documentation — but no book. I
started asking AIs about it, half-expecting to find someone quietly writing one.
Every conversation ended the same way: me expressing disbelief, and the model
offering some variation of "Yes, it's a strange gap. You know, I could write
that book — want me to?"

One day, I took Claude up on the offer.

You don't one-shot a book. What followed was a long collaboration — iterative,
occasionally humbling, and genuinely educational. The structural skeleton came
from an unlikely source: a framework I'd built to produce a [family cookbook](https://github.com/hardyoyo/RodmanPottingerCookbook)[^cookbook], assembled with
Pandoc, Markdown, and yes, a Makefile. That same toolchain could hold a
technical book together just as well as a collection of family recipes.

John became this book's first serious reader and an official collaborator,
including on a talk we'll be giving together at UC-Tech in July 2026. He is, I
should mention, deeply suspicious of AI. He is also the kind of tinkerer who
runs his own local models with Ollama. His feedback made this book sharper, more
honest, and more useful.

I learned a lot editing it. I hope you learn a lot reading it.

--Hardy

[^vagrant]: https://github.com/jhriv/vagrant-as-infrastructure
[^cookbook]: https://github.com/hardyoyo/RodmanPottingerCookbook
