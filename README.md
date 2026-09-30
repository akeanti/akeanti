<a name="top"></a>

<p>
<img src="./assets/cover.svg" width="100%" alt="Akeanti | Electrical and energy engineering at EHTP | Now building: graph learning for grid cascades, PEM electrolyzer fault diagnostics, OT / SCADA anomaly detection | Open to internships, summer 2027">
</p>

<p>
<a href="#whats-next"><img src="./assets/ticker.svg" width="100%" alt="Lab wire. Shipped: cascade-gnn v0.3 with 14 tests passing in CI. On the bench: OT / SCADA anomaly-detection dashboard. Next: cascade-gnn on the official PowerGraph data. Open: summer 2027 internship, 1–2 months. Cooking: something new; follow to catch it."></a>
</p>

<p align="center">
  <a href="https://github.com/akeanti/cascade-gnn"><img src="./assets/button-project.svg" width="18%" alt="Open my flagship project, cascade-gnn"></a>
  <a href="mailto:akeantie@gmail.com?subject=CV%20request%3A%20%5Bcompany%5D%20internship&amp;body=Hi%20Akeanti%2C%0D%0A%0D%0ACould%20you%20send%20me%20your%20CV%3F%0D%0A%0D%0ACompany%3A%0D%0ARole%20%2F%20team%3A%0D%0AInternship%20dates%3A%0D%0ALocation%20%2F%20work%20mode%3A%0D%0A%0D%0AThanks%2C"><img src="./assets/button-cv.svg" width="18%" alt="Request my CV by email"></a>
  <a href="#role-fit"><img src="./assets/button-role.svg" width="18%" alt="See which roles I fit"></a>
  <a href="#whats-next"><img src="./assets/button-next.svg" width="18%" alt="See what’s next"></a>
  <a href="mailto:akeantie@gmail.com"><img src="./assets/button-email.svg" width="18%" alt="Email me"></a>
</p>

<p align="center">
  <b>Measurements in. Explainable models out.</b><br>
  <sub>Electrical &amp; energy engineering student at EHTP · diagnostics for power grids and electrolyzers · ideas tested on the bench</sub>
</p>

<p>
<a href="#recruiter-desk"><img src="./assets/snapshot.svg" width="100%" alt="At a glance: open to a summer 2027 internship of 1–2 months in electrical and energy engineering, industrial AI or OT security. Morocco or abroad; on-site, hybrid or remote. EHTP (GEE), after CPGE MP and the CNC. Arabic native, French fluent, English professional."></a>
</p>

<a name="selected-work"></a>

<p>
<img src="./assets/section-proof.svg" width="100%" alt="01 · Proof: Selected work.">
</p>

<p>
<img src="./assets/impact.svg" width="100%" alt="Evidence, not adjectives: 23% wireless-power efficiency at 34 kHz on my TIPE prototype; R² = 0.992 against the Yates reference in a model comparison; 5 graph architectures benchmarked against XGBoost in cascade-gnn; 14 automated tests passing in CI.">
</p>

<p align="center">
  <a href="https://github.com/akeanti/cascade-gnn"><img src="./assets/grid-card.svg" width="49%" alt="cascade-gnn: graph learning for cascading grid failures. Opens the repository."></a>
  <a href="#pem-project"><img src="./assets/pem-card.svg" width="49%" alt="PEM electrolyzer fault diagnostics with current analysis, XGBoost and SHAP."></a>
</p>

### Grid project

<p>
<a href="https://github.com/akeanti/cascade-gnn/actions"><img src="https://img.shields.io/github/actions/workflow/status/akeanti/cascade-gnn/ci.yml?branch=main&label=tests&style=flat-square&labelColor=181e1c" alt="Tests status"></a>
<img src="https://img.shields.io/badge/release-v0.3.0-b7cd91?style=flat-square&labelColor=181e1c" alt="Release v0.3.0">
<img src="https://img.shields.io/badge/python-3.12_|_3.13-b7cd91?style=flat-square&labelColor=181e1c" alt="Python 3.12 and 3.13">
<img src="https://img.shields.io/badge/docker-ready-b7cd91?style=flat-square&labelColor=181e1c" alt="Docker ready">
<img src="https://img.shields.io/github/license/akeanti/cascade-gnn?style=flat-square&labelColor=181e1c&color=b7cd91" alt="MIT license">
<a href="https://github.com/akeanti/cascade-gnn/blob/main/docs/CLAIMS.md"><img src="https://img.shields.io/badge/claim%20ledger-read-48bfc4?style=flat-square&labelColor=181e1c" alt="Read the claim ledger"></a>
</p>

**[cascade-gnn](https://github.com/akeanti/cascade-gnn)**: early warning for cascading failures in power grids, built on the **PowerGraph** (NeurIPS 2024) dataset.

- **Problem:** after an initial outage, will the grid fail to serve demand, or cascade into more branch trips?
- **Approach:** five graph neural network variants against **XGBoost** baselines; random, operating-condition and contingency-grouped splits with **leakage checks**; **gradient × input** and **integrated-gradients** edge attributions scored against the simulated cascade; a **Streamlit** demo.
- **Result:** v0.3 runs end to end with **14 passing tests in CI**, Docker, and a claim ledger that separates what the code shows from what still needs the official PowerGraph runs. No benchmark score is claimed yet.
- **Stack:** Python · PyTorch · XGBoost · scikit-learn · Streamlit · Docker · GitHub Actions · LaTeX

<p>
<a href="https://github.com/akeanti/cascade-gnn"><img src="./assets/pipeline.svg" width="100%" alt="Inside cascade-gnn, eight stages: ingest PowerGraph targets; audit the data contract; three split strategies; leakage checks; five GNNs vs XGBoost on the same split; temperature scaling; edge attributions checked against the simulated cascade; repeated runs, manifests and a Streamlit demo."></a>
</p>

### PEM project

A student competition project on **fault diagnostics for PEM electrolyzers**.

- **Problem:** spot faults in a PEM electrolyzer from its electrical current signals.
- **Approach:** **MCSA-inspired** current-signal features, an **XGBoost** classifier, and **SHAP** to show which features drive each prediction.
- **Stack:** Python · signal processing · XGBoost · SHAP

<p align="center">
  <a href="#bench-notes"><img src="./assets/wpt-card.svg" width="49%" alt="TIPE wireless power: 23% efficiency at 34 kHz, with R² = 0.992 against the Yates reference."></a>
  <a href="#what-i-bring"><img src="./assets/fit-card.svg" width="49%" alt="Hardware, code and maths: practical work, model comparisons and explanations."></a>
</p>

### Bench notes

My **TIPE** project: a resonant **wireless power transfer** prototype, built and measured on the bench.

- **Result:** **23% efficiency at 34 kHz**, with **R² = 0.992** in a model comparison against the Yates reference.
- **In progress:** an **OT / SCADA anomaly-detection dashboard**.

<p align="right"><sub><a href="#top">↑ back to top</a></sub></p>

<a name="role-fit"></a>

<p>
<img src="./assets/section-fit.svg" width="100%" alt="02 · Fit: Where I fit.">
</p>

<p>
<img src="./assets/role-fit.svg" width="100%" alt="Hiring for…? Power systems and grid analytics: cascade-gnn. Energy and hydrogen systems: PEM diagnostics. Power electronics and test bench: WPT prototype. Industrial AI and data: cascade-gnn and PEM diagnostics. OT / ICS security: OT / SCADA dashboard, in progress. Embedded and instrumentation: CPGE-Robotics.">
</p>

| If you're hiring for… | Start here |
| :-- | :-- |
| **Power systems & grid analytics** | [cascade-gnn](https://github.com/akeanti/cascade-gnn) · [how it works](#grid-project) |
| **Energy & hydrogen systems** | [PEM diagnostics](#pem-project) |
| **Power electronics & test bench** | [WPT prototype: 23% at 34 kHz](#bench-notes) |
| **Industrial AI & data** | [cascade-gnn](https://github.com/akeanti/cascade-gnn) · [PEM diagnostics](#pem-project) |
| **OT / ICS security** | OT / SCADA anomaly-detection dashboard *(in progress)* · Nmap · Wireshark |
| **Embedded & instrumentation** | [CPGE-Robotics](https://github.com/akeanti/CPGE-Robotics) · ESP32 · ADS1115 |

### What I bring

- **Hardware and code, together.** My projects connect resonant power transfer, embedded acquisition, signal analysis, and Python-based modelling.
- **Results I can defend.** I use baselines, grouped splits, integrated gradients and SHAP to check what a model is really doing, and I write down which claims the evidence supports.
- **A maths foundation and work on the bench.** CPGE MP gave me the foundations. The WPT prototype and diagnostic projects give me a place to apply them, test things, and improve.

The internship I’m looking for has room for both a notebook and a workbench. I’d be glad to help with measurements, prototypes, data analysis, or diagnostic tools, and learn from the engineers around me.

<p>
<a href="mailto:akeantie@gmail.com?subject=Internship%20conversation"><img src="./assets/ask-me.svg" width="100%" alt="Ask me about: why a tuned XGBoost can beat a GNN; keeping ML results honest with grouped splits, leakage checks and a claim ledger; building a 34 kHz WPT prototype and comparing it to the Yates reference. Click to email me."></a>
</p>

<p align="right"><sub><a href="#top">↑ back to top</a></sub></p>

<a name="whats-next"></a>

<p>
<img src="./assets/section-next.svg" width="100%" alt="03 · Next: What’s next. More is cooking, stay tuned.">
</p>

<p>
<img src="./assets/next-bench.svg" width="100%" alt="Next on the bench. Shipped in August 2026: cascade-gnn v0.3. On the bench: OT / SCADA anomaly-detection dashboard. Next milestone: cascade-gnn on the official PowerGraph data. Under wraps: something new is cooking; reveal soon.">
</p>

<p align="center">
  <b>Stay tuned: I’m cooking more, and this board fills up as the work ships.</b><br>
  <sub>Hit <b>Follow</b> on this profile to catch the next release.</sub>
</p>

<p align="center">
  <a href="https://github.com/akeanti/akeanti/commits/main"><img src="https://img.shields.io/github/last-commit/akeanti/akeanti?label=profile%20updated&style=flat-square&labelColor=181e1c&color=48bfc4" alt="Profile last updated"></a>
</p>

<p align="right"><sub><a href="#top">↑ back to top</a></sub></p>

<a name="it-started-with-a-pc"></a>

<p>
<img src="./assets/section-story.svg" width="100%" alt="04 · Story: It started with a PC.">
</p>

I was **six when I opened my dad’s old PC**. I wanted to know what was inside, and electronics became something I kept coming back to.

Now I study **Génie Électrique et Énergétique at EHTP**, after **CPGE MP** and the **CNC**. I’m interested in how measurements from real equipment can help us understand faults. That has led me to projects on power grids, electrolyzers, and wireless power transfer.

<p align="center">
  <a href="#it-started-with-a-pc"><img src="./assets/origin.svg" width="49%" alt="Where it started: opening my dad’s old PC at six."></a>
  <a href="#my-mission"><img src="./assets/mission.svg" width="49%" alt="My mission: better diagnostics, less wasted energy and more reliable electrical systems."></a>
</p>

### My mission

I want to help electrical systems waste less energy and catch problems earlier. That starts with understanding the hardware, getting useful measurements, and building models whose results people can make sense of. That's the kind of engineering I want to get good at.

<p>
<img src="./assets/journey.svg" width="100%" alt="Age six: dad’s old PC → CPGE MP → TIPE wireless-power experiments → EHTP → Current grid and PEM projects.">
</p>

<p align="right"><sub><a href="#top">↑ back to top</a></sub></p>

<a name="how-i-work"></a>

<p>
<img src="./assets/section-method.svg" width="100%" alt="05 · Method: How I work.">
</p>

<p>
<img src="./assets/workflow.svg" width="100%" alt="Measure → Model → Compare → Explain → Review. Embedded acquisition, models, baseline comparisons, explanations and Streamlit.">
</p>

<p>
<img src="./assets/toolbox.svg" width="100%" alt="Tools for power and energy, machine learning, embedded systems, industrial security and software development.">
</p>

<p align="right"><sub><a href="#top">↑ back to top</a></sub></p>

<a name="code-in-the-open"></a>

<p>
<img src="./assets/section-code.svg" width="100%" alt="06 · Code: Open source.">
</p>

<p>
<a href="https://github.com/akeanti?tab=repositories"><img src="./assets/open-source.svg" width="100%" alt="Code in the open: cascade-gnn, CPGE-Robotics, and a maths wiki, plus LaTeX and Advent of Code 2025."></a>
</p>

| Project | What it is |
| :-- | :-- |
| [**cascade-gnn**](https://github.com/akeanti/cascade-gnn) | Graph neural networks vs XGBoost for cascading grid failures on PowerGraph, with edge attributions, CI tests and a Streamlit demo. |
| [**CPGE-Robotics**](https://github.com/akeanti/CPGE-Robotics) | Arduino projects from the prépa robotics club. |
| [**Maths wiki**](https://akeanti.github.io/Maths-Ain-t-Mathing-Wiki/) | My own maths notes, written up as a wiki. |
| [**LaTeX**](https://github.com/akeanti/LaTeX) | Templates and documents I've typeset. |
| [**Advent of Code 2025**](https://github.com/akeanti/Advent-of-code-2025) | Python solutions with write-ups. |

<p align="right"><sub><a href="#top">↑ back to top</a></sub></p>

<a name="off-the-bench"></a>

<p>
<img src="./assets/section-off.svg" width="100%" alt="07 · Off the bench.">
</p>

I also enjoy competitive mathematics and metroidvania games. There’s usually another problem to get absorbed in. I draw around the things I work on too; the signals and scenes below are illustrations, and the project results are in the notes above.

<details>
<summary><b>Open the art notebook</b> · animated studies</summary>

<p>
<img src="./assets/workbench-scene.svg" width="100%" alt="An animated electronics workbench illustration: open PC, oscilloscope and layered circuit board.">
</p>

<p align="center">
  <a href="./assets/scope-study.svg"><img src="./assets/scope-study.svg" width="49%" alt="Open the oscilloscope artwork with a scanning trace and illustrative waveforms."></a>
  <a href="./assets/pcb-study.svg"><img src="./assets/pcb-study.svg" width="49%" alt="Open the exploded circuit-board artwork with moving traces and a floating chip."></a>
</p>

<p align="center">
  <a href="./assets/phase-study.svg"><img src="./assets/phase-study.svg" width="49%" alt="Open the Lissajous curve study with travelling highlights."></a>
  <a href="./assets/resonance-study.svg"><img src="./assets/resonance-study.svg" width="49%" alt="Open the generative toroidal field sculpture with slow rocking motion."></a>
</p>

<p align="center">
  <a href="./assets/notebook-study.svg"><img src="./assets/notebook-study.svg" width="49%" alt="Open the illustrated engineering notebook with an animated waveform."></a>
  <a href="./assets/after-hours.svg"><img src="./assets/after-hours.svg" width="49%" alt="Open the abstract exploration map inspired by my interest in mathematics and metroidvania games."></a>
</p>

<p>
<img src="./assets/connected-systems.svg" width="100%" alt="Conceptual energy-system panorama: generation, storage, the grid and control. Animated original artwork.">
</p>

</details>

<p align="right"><sub><a href="#top">↑ back to top</a></sub></p>

<a name="recruiter-desk"></a>
<a name="lets-talk"></a>

<p>
<img src="./assets/section-contact.svg" width="100%" alt="08 · Contact: Recruiter desk. One click to reach me.">
</p>

I'm looking for a **summer 2027 internship (1–2 months)** in electrical and energy engineering, industrial AI, or OT cybersecurity. **Morocco or abroad**, on-site, hybrid, or remote. I work in **Arabic, French and English**. **CV available on request.**

<p align="center">
  <a href="mailto:akeantie@gmail.com?subject=CV%20request%3A%20%5Bcompany%5D%20internship&amp;body=Hi%20Akeanti%2C%0D%0A%0D%0ACould%20you%20send%20me%20your%20CV%3F%0D%0A%0D%0ACompany%3A%0D%0ARole%20%2F%20team%3A%0D%0AInternship%20dates%3A%0D%0ALocation%20%2F%20work%20mode%3A%0D%0A%0D%0AThanks%2C"><img src="./assets/desk-cv.svg" width="32%" alt="Request my CV: opens a pre-filled email asking for company, role and dates."></a>
  <a href="mailto:akeantie@gmail.com?subject=Call%20about%20a%20%5Bcompany%5D%20internship&amp;body=Hi%20Akeanti%2C%0D%0A%0D%0AI%20would%20like%20to%20set%20up%20a%20short%20call%20about%20an%20internship.%0D%0A%0D%0ACompany%3A%0D%0ARole%20%2F%20team%3A%0D%0AProposed%20times%20(with%20time%20zone)%3A%0D%0AVideo%20link%20or%20phone%3A%0D%0A%0D%0ABest%2C"><img src="./assets/desk-call.svg" width="32%" alt="Book a call: opens a pre-filled email asking for proposed times, time zone and a call link."></a>
  <a href="mailto:akeantie@gmail.com?subject=Internship%20opportunity%3A%20%5Brole%5D%20at%20%5Bcompany%5D&amp;body=Hi%20Akeanti%2C%0D%0A%0D%0AWe%20have%20an%20internship%20that%20could%20fit%20your%20profile.%0D%0A%0D%0ACompany%3A%0D%0ARole%3A%0D%0ADates%20and%20duration%3A%0D%0ALocation%20%2F%20work%20mode%3A%0D%0ALink%20to%20the%20posting%3A%0D%0A%0D%0ABest%2C"><img src="./assets/desk-role.svg" width="32%" alt="Share a role: opens a pre-filled email asking for dates, location and a link to the posting."></a>
</p>

<p align="center"><sub>Each button opens a pre-filled email in your mail app. Fill in the blanks and send.</sub></p>

<details>
<summary><b>Recruiter FAQ</b> · quick answers</summary>

<br>

**When can you start, and for how long?**<br>
Summer 2027, for 1–2 months. Exact dates on request.

**Where can you work?**<br>
Morocco or abroad: on-site, hybrid or remote.

**Which languages do you work in?**<br>
Arabic (native), French (fluent) and English (professional).

**What are you studying?**<br>
Génie Électrique et Énergétique (electrical and energy engineering) at EHTP, after CPGE MP and the CNC.

**Which roles fit best?**<br>
Power systems, energy and hydrogen, power electronics, industrial AI, OT security and embedded work. See [Where I fit](#role-fit) for the evidence behind each.

**Can I verify your work?**<br>
Yes. cascade-gnn is public with its tests, CI and a [claim ledger](https://github.com/akeanti/cascade-gnn/blob/main/docs/CLAIMS.md). The numbers under [Selected work](#selected-work) come from my projects.

**Can I get your CV?**<br>
Yes: use **Request my CV** above and I'll send it by email.

</details>

<details>
<summary><b>Recruiter quick copy</b> · plain-text profile for your notes or ATS</summary>

```text
Akeanti | Electrical & energy engineering student, EHTP (GEE)
Background   CPGE MP · CNC
Looking for  Summer 2027 internship, 1–2 months
Fields       Electrical & energy engineering · industrial AI · OT security
Location     Morocco or abroad · on-site, hybrid or remote
Languages    Arabic (native) · French (fluent) · English (professional)
Highlights   Resonant WPT prototype: 23% efficiency at 34 kHz, R² = 0.992 vs Yates reference
             cascade-gnn: 5 GNN variants vs XGBoost on PowerGraph, 14 tests in CI, Docker
             PEM electrolyzer fault diagnostics: MCSA-inspired features, XGBoost, SHAP
Skills       Python, C++, Bash, PyTorch, PyTorch Geometric, XGBoost, SHAP, scikit-learn,
             ESP32, Arduino, ADS1115, SCADA, Nmap, Wireshark, Git, Linux, Docker, LaTeX
Keywords     power systems, grid resilience, fault diagnostics, hydrogen, PEM electrolyzer,
             wireless power transfer, signal processing, graph neural networks,
             explainable AI, industrial AI, OT security, SCADA, embedded systems
Contact      akeantie@gmail.com · github.com/akeanti · CV on request
```

</details>

<p>
<a href="mailto:akeantie@gmail.com"><img src="./assets/contact-strip.svg" width="100%" alt="Let’s talk about an internship. Click to email Akeanti."></a>
</p>

<p align="center">
  <a href="mailto:akeantie@gmail.com"><b>akeantie@gmail.com</b></a> &nbsp;·&nbsp;
  <a href="https://github.com/akeanti/cascade-gnn"><b>cascade-gnn</b></a> &nbsp;·&nbsp;
  <a href="#top"><b>back to top ↑</b></a>
</p>

<p align="center"><sub>Personal site, less formal: <a href="https://akeanti.xyz">akeanti.xyz</a></sub></p>
