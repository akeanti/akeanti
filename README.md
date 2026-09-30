<p>
<img src="./assets/cover.svg" width="100%" alt="Akeanti | Electrical and energy engineering at EHTP | Now building: graph learning for grid cascades, PEM electrolyzer fault diagnostics, OT / SCADA anomaly detection | Open to internships, summer 2027">
</p>

<p align="center">
  <a href="https://github.com/akeanti/cascade-gnn"><img src="./assets/button-project.svg" width="18%" alt="Open my flagship project, cascade-gnn"></a>
  <a href="mailto:akeantie@gmail.com"><img src="./assets/button-email.svg" width="18%" alt="Email me"></a>
  <a href="#selected-work"><img src="./assets/button-work.svg" width="18%" alt="See selected work"></a>
  <a href="#what-i-bring"><img src="./assets/button-fit.svg" width="18%" alt="Read what I could bring to your team"></a>
  <a href="#code-in-the-open"><img src="./assets/button-code.svg" width="18%" alt="See my open-source code"></a>
</p>

<p>
<a href="#lets-talk"><img src="./assets/snapshot.svg" width="100%" alt="At a glance: open to a summer 2027 internship of 1–2 months in electrical and energy engineering, industrial AI or OT security. Morocco or abroad; on-site, hybrid or remote. EHTP (GEE), after CPGE MP and the CNC. Arabic native, French fluent, English professional."></a>
</p>

## Selected work

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
- **Approach:** five graph neural network variants against **XGBoost** baselines; random, operating-condition and contingency-grouped splits with **leakage checks**; **GNNExplainer** edge attributions compared with the simulated cascade; a **Streamlit** demo.
- **Result:** v0.3 runs end to end with **14 passing tests in CI**, Docker, and a claim ledger that separates what the code shows from what still needs the official PowerGraph runs. No benchmark score is claimed yet.
- **Stack:** Python · PyTorch · XGBoost · scikit-learn · Streamlit · Docker · GitHub Actions · LaTeX

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

## What I bring

- **Hardware and code, together.** My projects connect resonant power transfer, embedded acquisition, signal analysis, and Python-based modelling.
- **Results I can defend.** I use baselines, grouped splits, GNNExplainer and SHAP to check what a model is really doing, and I write down which claims the evidence supports.
- **A maths foundation and work on the bench.** CPGE MP gave me the foundations. The WPT prototype and diagnostic projects give me a place to apply them, test things, and improve.

The internship I’m looking for has room for both a notebook and a workbench. I’d be glad to help with measurements, prototypes, data analysis, or diagnostic tools, and learn from the engineers around me.

<p>
<a href="mailto:akeantie@gmail.com?subject=Internship%20conversation"><img src="./assets/ask-me.svg" width="100%" alt="Ask me about: why a tuned XGBoost can beat a GNN; keeping ML results honest with grouped splits, leakage checks and a claim ledger; building a 34 kHz WPT prototype and comparing it to the Yates reference. Click to email me."></a>
</p>

## It started with a PC

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

## How I work

<p>
<img src="./assets/workflow.svg" width="100%" alt="Measure → Model → Compare → Explain → Review. Embedded acquisition, models, baseline comparisons, explanations and Streamlit.">
</p>

<p>
<img src="./assets/toolbox.svg" width="100%" alt="Tools for power and energy, machine learning, embedded systems, industrial security and software development.">
</p>

## Code in the open

<p>
<a href="https://github.com/akeanti?tab=repositories"><img src="./assets/open-source.svg" width="100%" alt="Code in the open: cascade-gnn, CPGE-Robotics, and a maths wiki, plus LaTeX and Advent of Code 2025."></a>
</p>

| Project | What it is |
| :-- | :-- |
| [**cascade-gnn**](https://github.com/akeanti/cascade-gnn) | Graph neural networks vs XGBoost for cascading grid failures on PowerGraph, with GNNExplainer, CI tests and a Streamlit demo. |
| [**CPGE-Robotics**](https://github.com/akeanti/CPGE-Robotics) | Arduino projects from the prépa robotics club. |
| [**Maths wiki**](https://akeanti.github.io/Maths-Ain-t-Mathing-Wiki/) | My own maths notes, written up as a wiki. |
| [**LaTeX**](https://github.com/akeanti/LaTeX) | Templates and documents I've typeset. |
| [**Advent of Code 2025**](https://github.com/akeanti/Advent-of-code-2025) | Python solutions with write-ups. |

<img src="./assets/divider.svg" width="100%" alt="">

## Off the bench

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

## Let's talk

I'm looking for a **summer 2027 internship (1–2 months)** in electrical and energy engineering, industrial AI, or OT cybersecurity. **Morocco or abroad**, on-site, hybrid, or remote. I work in **Arabic, French and English**.

**CV available on request**: just email me and I'll send it over.

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
Contact      akeantie@gmail.com · github.com/akeanti · CV on request
```

</details>

<p>
<a href="mailto:akeantie@gmail.com"><img src="./assets/contact-strip.svg" width="100%" alt="Let’s talk about an internship. Click to email Akeanti."></a>
</p>

<p align="center">
  <a href="mailto:akeantie@gmail.com"><b>akeantie@gmail.com</b></a> &nbsp;·&nbsp;
  <a href="https://github.com/akeanti/cascade-gnn"><b>cascade-gnn</b></a>
</p>

<p align="center"><sub>Personal site, less formal: <a href="https://akeanti.xyz">akeanti.xyz</a></sub></p>
