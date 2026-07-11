---
marp: true
theme: default
size: 16:9
paginate: true
html: true
title: 'DrowsyGuard: Secure Driver Drowsiness Detection'
style: |
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;800&display=swap');

  :root {
    --primary:  #2C1810;
    --accent:   #B8753A;
    --accent2:  #7A4520;
    --light:    #E8D5B7;
    --text:     #1A0E08;
    --muted:    #4a3828;
    --bg:       #ffffff;
  }

  section {
    font-family: 'Segoe UI', Arial, sans-serif;
    color: var(--text);
    background: var(--bg);
    padding: 48px 64px;
  }

  h1, h2, h3 {
    font-family: 'Playfair Display', Georgia, serif;
    color: var(--primary);
    letter-spacing: -0.01em;
  }

  h1 { font-size: 1.9em; border-bottom: 3px solid var(--accent); padding-bottom: 0.2em; }
  h2 { font-size: 1.35em; color: var(--accent2); }
  h3 { font-size: 1.05em; color: var(--primary); }

  a { color: var(--accent2); }

  strong { color: var(--primary); }

  section.lead {
    background: var(--primary);
    color: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  section.lead h1 {
    color: #ffffff;
    border-bottom: 3px solid var(--accent);
    font-size: 2.6em;
  }
  section.lead h2 { color: var(--light); font-weight: 400; font-style: italic; }
  section.lead p { color: rgba(255,255,255,0.85); }
  section.lead .tag {
    display: inline-block;
    background: rgba(255,255,255,0.12);
    color: var(--light);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 0.6em;
    margin-right: 8px;
    margin-top: 12px;
  }

  section.section {
    background: var(--primary);
    color: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  section.section h1 {
    color: #ffffff;
    font-size: 2.4em;
    border-bottom: 3px solid var(--accent);
    display: inline-block;
  }
  section.section .kicker {
    color: var(--accent);
    text-transform: uppercase;
    letter-spacing: 0.15em;
    font-size: 0.75em;
    font-weight: 700;
    margin-bottom: 6px;
  }
  section.section p { color: rgba(255,255,255,0.82); font-size: 0.95em; }

  .cols {
    display: flex;
    gap: 32px;
    margin-top: 10px;
  }
  .cols > div { flex: 1; }

  .box {
    background: var(--light);
    border-left: 4px solid var(--accent2);
    border-radius: 4px;
    padding: 10px 16px;
    margin: 6px 0;
    font-size: 0.85em;
    color: var(--text);
  }

  .pipeline {
    display: flex;
    align-items: center;
    gap: 6px;
    flex-wrap: wrap;
    margin: 14px 0;
  }
  .pipeline .step {
    background: var(--primary);
    color: #fff;
    border-radius: 6px;
    padding: 8px 14px;
    font-size: 0.72em;
    font-weight: 600;
    text-align: center;
  }
  .pipeline .arrow { color: var(--accent2); font-size: 1.1em; font-weight: 700; }

  table { font-size: 0.72em; border-collapse: collapse; width: 100%; }
  th { background: var(--primary); color: #fff; padding: 6px 10px; text-align: left; }
  td { padding: 5px 10px; border-bottom: 1px solid var(--light); }
  tr:nth-child(even) td { background: #faf6ef; }

  .metric {
    display: inline-block;
    background: var(--primary);
    color: #fff;
    border-radius: 6px;
    padding: 10px 18px;
    margin: 4px 8px 4px 0;
    text-align: center;
  }
  .metric .n { font-size: 1.3em; font-weight: 800; color: var(--light); display: block; }
  .metric .l { font-size: 0.55em; text-transform: uppercase; letter-spacing: 0.08em; color: rgba(255,255,255,0.75); }

  .kv { font-size: 0.85em; line-height: 1.9; }
  .kv b { color: var(--accent2); }

  ul, ol { font-size: 0.9em; line-height: 1.55; }
  li::marker { color: var(--accent2); }

  .small { font-size: 0.7em; color: var(--muted); }

  .bug { border-left: 4px solid #a33; background: #fbeeee; }
  .fix { border-left: 4px solid #2d7d3a; background: #eef7ef; }
---

<!-- _class: lead -->

# DrowsyGuard
## Secure Driver Drowsiness Detection

Embedded Systems & IoT Security, Course Project

<span class="tag">Raspberry Pi (emulated)</span><span class="tag">TinyML / TFLite</span><span class="tag">AES-256-CBC</span><span class="tag">Arduino Uno R4 WiFi</span>

<!--
Welcome. This is DrowsyGuard, a secure driver drowsiness detection system,
built for the Embedded Systems and IoT Security course. It's an
architectural clone of the example fire-detector project, adapted to a
different domain: detecting when a driver is falling asleep at the wheel.

Ten minutes total. I'll walk through: the problem, the architecture, how
it was built (TDD), the model and its real results, the security layer,
the physical Arduino companion, and what I learned building it end to end
on real hardware.
-->

---

# The Problem

<div class="cols">
<div>

- Driver fatigue is a major cause of road accidents
- Needs to run **on embedded hardware**, in real time, with **no cloud dependency**
- Must be **secure**: telemetry leaving the vehicle has to be encrypted
- Must be **testable**: safety-critical logic can't be "trust me, it works"

</div>
<div>

<div class="box">
<b>Goal:</b> real-time system on a Raspberry Pi (emulated here) that
detects drowsiness via a CNN and triggers an alarm: a local buzzer and
an encrypted MQTT alert to a companion device.
</div>

</div>
</div>

<!--
The motivation is straightforward: driver drowsiness is a real safety
problem, and a monitoring system for it has three hard constraints that
shaped every design decision here. It has to run on constrained embedded
hardware in real time. It has to be secure, because we're sending alerts
over the network. And it has to be testable, because this is the kind of
code where a silent bug means the alarm just doesn't go off.
-->

---

<!-- _class: section -->

<div class="kicker">01</div>

# Architecture

<p>Five components, one responsibility each</p>

<!--
Let's start with how the system is put together.
-->

---

# Five SRP Components

<div class="pipeline">
<div class="step">FrameProvider</div><div class="arrow">&rarr;</div>
<div class="step">ImageProcessor</div><div class="arrow">&rarr;</div>
<div class="step">InferenceEngine</div><div class="arrow">&rarr;</div>
<div class="step">DrowsinessMonitor</div><div class="arrow">&rarr;</div>
<div class="step">AlertNotifier</div>
</div>

<div class="kv">
<b>FrameProvider</b>: video/webcam frame acquisition (OpenCV)<br>
<b>ImageProcessor</b>: resize, color conversion, luminance transform<br>
<b>InferenceEngine</b>: TFLite interpreter, runs the CNN<br>
<b>DrowsinessMonitor</b>: orchestrator, smoothing window + threshold decision<br>
<b>AlertNotifier</b>: buzzer (PWM/GPIO) + encrypted MQTT telemetry
</div>

<p class="small">No physical hardware required to run: GPIO is mocked (<code>mocks/GPIO.py</code>), with a
try/except fallback to the real <code>RPi.GPIO</code> when actually deployed on a Pi.</p>

<!--
Same pattern as the fire-detector template, applied to this domain. Each
box is a class with one job, wired together by dependency injection. That
last point about mocked GPIO is what makes this whole thing testable and
runnable on a laptop with zero physical hardware -- the code that would
run on a real Pi imports RPi.GPIO, and everywhere else, including this
entire development machine, it silently falls back to a mock with the
same interface.
-->

---

# Built Test-First (TDD)

<div class="cols">
<div>

**Red → Green → Refactor**, component by component.

- Every component has its own dependency-injected mock:
  `MockBuzzer`, mocked `cv2.VideoCapture`, mocked `tflite.Interpreter`
- **28 automated tests**, all green:
  - 22 Python (`unittest.mock`)
  - 6 Arduino / C++ (Unity, native PlatformIO env, no hardware needed)

</div>
<div>

<div class="metric"><span class="n">28 / 28</span><span class="l">tests passing</span></div>
<div class="metric"><span class="n">2</span><span class="l">test frameworks</span></div>

<div class="box">
Static analysis (flake8 + pylint) is part of the workflow, not an
afterthought: real tool findings only, no subjective "code smell" calls.
</div>

</div>
</div>

<!--
Testability was a first-class requirement, not an afterthought. Every
component is built against an interface, not a concrete hardware
dependency, so it can be driven by a mock in a unit test. That's true on
both the Python side and the Arduino C++ side, which has its own native
Unity test suite that runs entirely on the PC, no board required.

I also want to flag: static analysis findings you'll see later in this
talk all come from actually running flake8 and pylint, not from me
eyeballing the code and guessing what looks wrong.
-->

---

<!-- _class: section -->

<div class="kicker">02</div>

# The Model

<p>Preprocessing, architecture, and honest results</p>

<!--
Now the perception side: how the system actually decides "drowsy" or not.
-->

---

# Preprocessing & Model

<div class="cols">
<div>

**Preprocessing: a deliberate detour.** Tried and abandoned: Haar-cascade
eye cropping (~80% discard rate, and a **segfault** when cascade detection
runs alongside TensorFlow, confirmed and reproducible).
**Final:** full frame, resize 96×96, custom **[Y, B, R]** tensor (luminance
+ raw blue + raw red: 3 channels were mandatory anyway for the GPU
backend, so real signal fills all three instead of a duplicate).

</div>
<div>

**Model.** Custom CNN, **341,121 parameters** (under the 2M budget),
**no transfer learning**. Dataset: HuggingFace `driver-drowsiness-dataset`,
18,492 train / 2,311 val / 2,313 test.

<div class="box">
Counter-intuitive: <code>class_weight='balanced'</code> made results
<b>worse</b>, not better, interacted badly with early-stopping. Final
config: no class weighting.
</div>

</div>
</div>

<!--
Two quick things here. First, preprocessing: cropping to the eye region
with a Haar cascade seemed obviously right, but it discarded most of the
dataset and, worse, segfaulted whenever it ran alongside TensorFlow -- a
real, reproducible native library conflict. So the final pipeline uses
the full frame, transformed into three channels: luminance, raw blue, raw
red -- forced by a GPU constraint that rejects single-channel input
anyway, so the third channel carries real signal instead of a duplicate.

Second, the model itself: intentionally small, under two million
parameters, no pretrained backbone. One counter-intuitive finding worth
mentioning: I expected class weighting to help with class imbalance, and
instead it made the recall gap wider, interacting badly with early
stopping. Removing it gave the most balanced result of any run.
-->

---

# Results, Honest Numbers

<div class="cols">
<div>

<div class="metric"><span class="n">75.8%</span><span class="l">accuracy</span></div>
<div class="metric"><span class="n">0.756</span><span class="l">macro F1</span></div>
<div class="metric"><span class="n">0.751 / 0.764</span><span class="l">recall (not-drowsy / drowsy)</span></div>

<p class="small">Below the original 85% target, kept as-is deliberately: balanced
recall on both classes matters more here than a higher but skewed accuracy.</p>

</div>
<div>

<table>
<tr><th></th><th>precision</th><th>recall</th><th>f1</th></tr>
<tr><td>not_drowsy</td><td>0.710</td><td>0.751</td><td>0.730</td></tr>
<tr><td>drowsy</td><td>0.799</td><td>0.764</td><td>0.781</td></tr>
</table>

</div>
</div>

<!--
I'm presenting this deliberately as-is rather than rounding up. 75.8%
accuracy, below the original 85% target. What I'd emphasize is that the
two classes are fairly balanced -- recall of 0.75 and 0.76 -- which for a
safety alarm matters more than a higher accuracy that comes from being
much better at one class than the other. Training was paused here as a
deliberate checkpoint rather than chasing the number further this
session.
-->

---

<!-- _class: section -->

<div class="kicker">03</div>

# Security

<p>Encrypted telemetry, and an adversarial attack</p>

<!--
Moving to the IoT security half of the course requirements.
-->

---

# Security in Practice

<div class="cols">
<div>

**Encrypted telemetry.**

<div class="pipeline">
<div class="step">AlertNotifier</div><div class="arrow">&rarr;</div>
<div class="step">AES-256-CBC</div><div class="arrow">&rarr;</div>
<div class="step">Mosquitto</div><div class="arrow">&rarr;</div>
<div class="step">Node-RED</div>
</div>

Cross-language interop verified: encrypted in Python (<code>pycryptodome</code>),
decrypted in JavaScript (<code>crypto.createDecipheriv</code>), real payloads,
live dashboard at <code>localhost:1880/ui</code>.

</div>
<div>

**Attack &amp; defense.** PGD-style adversarial patch (20×20, 50 steps)
vs. Gaussian blur sanitization:

<table>
<tr><th>Stage</th><th>P(drowsy)</th><th>Correct?</th></tr>
<tr><td>Baseline</td><td>0.41</td><td>✓</td></tr>
<tr><td>Patched</td><td>0.998</td><td>✗ flipped</td></tr>
<tr><td>Sanitized</td><td>0.48</td><td>✓ restored</td></tr>
</table>

</div>
</div>

<!--
Two security pieces here. First: on detection, AlertNotifier doesn't just
flip a GPIO pin, it publishes an encrypted telemetry payload over MQTT --
AES-256-CBC, verified working across two languages, Python encrypting and
JavaScript decrypting inside Node-RED, feeding a live dashboard. That's a
real cross-language round trip, not just unit-tested in isolation.

Second: a demonstrated adversarial vulnerability. A genuinely not-drowsy
sample, correctly classified at 0.41, gets pushed to 0.998 by a small
optimized patch -- the model now confidently says "drowsy" on a clean
sample. A simple Gaussian blur, no retraining, restores the correct
prediction. Small, cheap defense, but an effective demonstration of both
the vulnerability and a practical mitigation.
-->

---

<!-- _class: section -->

<div class="kicker">04</div>

# The Physical Half

<p>Arduino Uno R4 WiFi, real hardware, real bugs</p>

<!--
Now for the part that only exists because I pushed this onto real
hardware instead of stopping at "it works in the emulator."
-->

---

# Arduino Companion

<div class="pipeline">
<div class="step">MQTT receive</div><div class="arrow">&rarr;</div>
<div class="step">AES-256-CBC decrypt</div><div class="arrow">&rarr;</div>
<div class="step">TelemetryHandler</div><div class="arrow">&rarr;</div>
<div class="step">LED matrix alarm</div>
</div>

<div class="kv">
<b>Why:</b> the Pi's own buzzer is mocked/didactic; the <b>real</b> physical alarm
is this board reacting to encrypted MQTT<br>
<b>tiny-AES-c</b> (vendored, forced to AES-256) decrypts on-device<br>
<b>Built-in 12×8 LED matrix</b> stands in for the buzzer, not wired yet
</div>

<!--
The Raspberry Pi side runs entirely emulated in this project -- no
physical Pi, mocked GPIO throughout. So to have a genuinely physical
alarm, I built a companion: an Arduino Uno R4 WiFi that subscribes to
the same encrypted MQTT topic, decrypts it on-device with a vendored
AES implementation, and drives an alarm. Since I don't have a physical
buzzer wired up yet, it temporarily drives the board's built-in LED
matrix instead -- same interface, swappable later, clearly marked as
temporary in the code.
-->

---

# Three Real Bugs, Found on Real Hardware

<div class="box bug"><b>1. Wrong WiFi SSID</b>: diagnosed by adding a temporary
<code>WiFi.scanNetworks()</code> dump; the board was silent over serial
before that, no logging existed at all.</div>

<div class="box bug"><b>2. LED matrix never lit</b>, despite MQTT→AES→handler all
confirmed working in the logs. Root cause: hardware timer allocation
happening in a <b>global object's constructor</b>: which runs before the
board's own clock/peripheral init. Silent failure, no error anywhere.</div>

<div class="box bug"><b>3. Model never triggered</b> on live webcam, even with eyes
closed. Root cause: live inference was feeding plain RGB, while the model
was trained on the <b>Y/B/R</b> transform, a preprocessing pipeline
mismatch invisible in unit tests (which never exercise the real camera path).</div>

<!--
None of these three bugs showed up in the unit test suite -- and that's
the point I want to make with this slide. All three only surfaced once
the system ran end to end on real hardware and real input. A wrong WiFi
network. A hardware timer silently failing because of C++ static
initialization order on this specific board. And the most interesting
one: the live camera pipeline and the training pipeline had quietly
diverged in what "correct" input looks like, and nothing in the test
suite could have caught that, because the tests never touch a real
camera frame. Physical bring-up earned its place in the schedule.
-->

---

# End-to-End, Live

<div class="pipeline">
<div class="step">Webcam</div><div class="arrow">&rarr;</div>
<div class="step">DrowsinessMonitor</div><div class="arrow">&rarr;</div>
<div class="step">Encrypted MQTT</div><div class="arrow">&rarr;</div>
<div class="step">Arduino</div><div class="arrow">&rarr;</div>
<div class="step">LED matrix ⚠</div>
</div>

Verified working, face close to the camera (dashboard-style framing).

<div class="box">
<b>Known limitation, not a bug:</b> the model needs the face to fill most
of the frame: training data is close-up crops, so a small/distant face
at 96×96 loses eye detail entirely. Documented as a deployment
constraint: mount the camera close to the driver, like a real DMS camera,
not a general-purpose room webcam.
</div>

<!--
This is the full loop, verified live: webcam feed in, through the
smoothing and threshold logic, out as an encrypted MQTT message, received
and decrypted by the physical Arduino, which lights its LED matrix. It
works, but I want to be upfront about a real limitation discovered during
testing: it only reacts reliably when the face fills most of the frame,
which matches how the training data was framed. This isn't a bug to
patch -- adding automatic face-cropping was tried before and abandoned
for the TensorFlow-segfault reason from two slides ago. It's documented
instead as a deployment constraint: this is a dashboard-mounted camera
system, not a general webcam.
-->

---

# Coverage-Driven Bug Hunt

<div class="cols">
<div>

Installed `coverage.py`, went from **91% → 98%** line coverage on `src/`
by writing tests for every gap, not to inflate a number, but because
the gaps themselves were the point.

Found **2 real bugs** this way, both fixed:

</div>
<div>

<div class="box bug"><b>1. Buzzer/GPIO never released on shutdown</b>:
<code>AlertNotifier.cleanup()</code> existed but was never called from
<code>DrowsinessMonitor</code>. Zero test exercised the shutdown path.</div>

<div class="box bug"><b>2. Arduino SIGSEGV on malformed input</b>:
<code>strncmp()</code> on a null <code>status</code> pointer when JSON is
valid but missing that field. Proven with an <b>actual crash</b>, not
just theoretical undefined behavior.</div>

</div>
</div>

<!--
This is a different kind of bug-hunting than the hardware one a couple
slides ago -- not "run it on real hardware and see what breaks," but
"deliberately go looking at what the test suite doesn't cover, and ask
why." Coverage numbers alone don't prove correctness, but the gaps they
point at are honest leads. Two real bugs came out of systematically
working through them: a cleanup path that silently never ran, and an
Arduino crash on malformed input that I reproduced with an actual
segfault before fixing it, not just reasoning about it in the abstract.
-->

---

# Engineering Practices

<div class="cols">
<div>

- **flake8**: 100% clean on `src/`
- **pylint**: refactored `AlertNotifier` (composition, `AlarmState` +
  `MqttConfig`) to fix a real `too-many-instance-attributes` finding
- Every fix traceable: what was found, by which tool, and who applied it
- `DrowsinessMonitor` deliberately **left alone**: same warning there
  would only silence the linter, not reflect an actual design problem

</div>
<div>

<div class="box">
Every commit message is scoped to <b>what changed and why</b>: no
noise, no unrelated bundling.
</div>

</div>
</div>

<!--
A quick note on process, since it's graded as much as the code is.
Static analysis findings were tracked with real tool output, not
subjective opinion, and every fix is logged with who applied it and why.
I also want to highlight a decision I'm proud of: DrowsinessMonitor
triggers the same linter warning as AlertNotifier did, but I deliberately
did not refactor it, because in that case the extra attributes are
already correct dependency-injected collaborators, not real state -- the
refactor would only have quieted the tool, not fixed anything real.
-->

---

# How AI Was Used

<div class="kv">
<b>Planning help</b>: structuring an effective work plan<br>
<b>Autonomous</b>: reviewing the tests<br>
<b>Autonomous</b>: reviewing code smells and other tool findings<br>
<b>Autonomous for low-hanging fruit, manual for complex cases</b>: patching findings<br>
<b>Autonomous</b>: writing commits and pushing after a prompt, updating progress docs<br>
<b>Autonomous</b>: reviewing code for hidden bugs / untested edge cases, then suggesting tests
</div>

<div class="box">
<b>Autonomous</b> = done by the AI after a prompt, no step-by-step supervision.
<b>Manual</b> = done by me, after the AI pointed it out.
</div>

<!--
Full transparency on how AI was used, since I think this matters as much
as the results. Planning was assisted. Test review, static-analysis
review, and hidden-bug/edge-case review were autonomous -- I'd ask, and
it would go look. Patching findings was autonomous for mechanical,
low-hanging-fruit fixes, but manual -- meaning I wrote the actual fix
myself -- for anything non-trivial, like the AlertNotifier refactor
decision or the Arduino null-check. Commits and progress-doc updates were
autonomous after I prompted for them. The actual implementation code in
src and the Arduino core stayed mine throughout, by design.
-->

---

<!-- _class: lead -->

# Thank You

## Questions?

<p class="small">DrowsyGuard, Embedded Systems &amp; IoT Security</p>

<!--
That's the full loop: five testable components, a lightweight custom CNN
with honestly reported results, encrypted telemetry with a demonstrated
attack and defense, and a physical Arduino companion that surfaced three
real bugs no unit test could have caught. Happy to take questions, or to
go deeper on any part of this -- the model, the security layer, or the
hardware bring-up.
-->
