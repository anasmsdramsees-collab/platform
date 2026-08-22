# Building the hub on a mini-PC

A prototype hub you assemble yourself, before there is anything to manufacture.
One machine, one house, real devices.

---

## 1. The machine

Nothing exotic. What the platform actually asks for:

| | Minimum | Why this and not less |
|---|---|---|
| **CPU** | x86-64, 4 cores | Home Assistant and the hub are both Python. Two cores works and leaves nothing spare while a model trains. |
| **RAM** | **8 GB** | Home Assistant takes ~1 GB, the hub ~500 MB, and the twin holds the house in memory. 4 GB runs until the day it does not. |
| **Storage** | 128 GB **SSD or NVMe** | Not an SD card and not a USB stick. Both die from write cycles, and the failure looks like a hub that has gone strange rather than a disk that has gone. |
| **Network** | Wired Ethernet | A hub on Wi-Fi is a hub that loses the house when the microwave runs. |
| **Power** | Anything, on a UPS | A hub that reboots on every flicker cannot watch for a gas leak. |

Fits, and commonly used for this: Intel N100 mini-PCs (Beelink, GMKtec, MinisForum) around 8 GB/256 GB, or an old office micro-PC — a Dell OptiPlex Micro or HP EliteDesk Mini for a fraction of the price. A Raspberry Pi 5 with an NVMe hat works; a Pi with an SD card does not, for the reason in the table.

### The radios

The mini-PC has no radios. Devices reach it through USB sticks, one per protocol:

| Protocol | What to buy | Devices |
|---|---|---|
| **Zigbee** | SONOFF ZBDongle-E, or a Home Assistant SkyConnect | Most affordable sensors, plugs, and bulbs |
| **Z-Wave** | Aeotec Z-Stick 7 | Locks and older sensors; longer range |
| **Thread / Matter** | SkyConnect (does Zigbee *or* Thread, not both at once) | New Matter devices |
| **Wi-Fi devices** | nothing to buy | They reach Home Assistant over the network |

**Start with Zigbee alone.** One stick, a handful of sensors and plugs, and the whole path from a real device to the wall panel is proven. Add the rest when the first one is boring.

**One warning worth the paragraph:** a USB 3 port and a Zigbee stick next to each other interfere badly — the symptom is devices that drop out at random, and it wastes days. Use a USB 2 port, or a short extension cable to move the stick away from the box.

---

## 2. What runs on it

```
mini-PC
├── Home Assistant   (docker)  ← talks to the radios and the devices
├── Mosquitto        (docker)  ← only if you have MQTT devices
└── syltra-hub       (systemd) ← the platform: twin, context, policy,
                                  safety, automations, scenes, goals,
                                  and the console and wall panel
```

The hub is **one process**. No NATS, no Postgres, no Prometheus — those belong to
the distributed deployment and a single house does not need them to prove
itself. `syltra_api_gateway/hub.py` explains what that drops and what it keeps;
the short version is that everything about safety is kept.

---

## 3. Installing

```bash
git clone <this repository> /tmp/syltra && cd /tmp/syltra/syltra-home-assistant
sudo ./infrastructure/scripts/install-hub.sh
```

It installs Docker and `uv`, creates a `syltra` user, syncs the dependencies
from the lockfile, and installs the systemd unit. Then it stops and asks you to
do two things by hand:

1. **Run Home Assistant** and set it up — the command is printed for you. Open
   `http://<machine>:8123`, create the account, plug in the Zigbee stick, add a
   device or two.
2. **Create a long-lived token** (Home Assistant → your profile → Security) and
   put it in `/etc/syltra/hub.env`.

The script does not do either. A script that creates your credentials is a
script that has put them somewhere.

Then:

```bash
sudo systemctl enable --now syltra-hub
journalctl -u syltra-hub -f
```

The log prints the console address and an owner token.

---

## 4. What you should see

Within a few seconds of starting, the log says the Edge Agent connected and how
many entities it mapped. Then:

- **`http://<machine>:8088/console/`** — the console. Paste the owner token into
  the browser console as the log tells you.
- **`http://<machine>:8088/panel/`** — the wall panel. Register it from the
  console's *Users and roles* screen to get a panel token, or open it on the
  tablet you intend to hang up and install it from the browser menu.

Press a light in Home Assistant and watch it change on the panel. Press it on
the panel and watch it change in Home Assistant. That round trip is the whole
platform working: Home Assistant → Edge Agent → twin → API → panel, and back
through policy, the orchestrator and the gateway.

---

## 5. What this prototype is not

Stated plainly, because finding these out on your own bench wastes a day each:

- **Tokens do not survive a restart.** `TokenStore` is in memory. Restarting the
  hub issues a new owner token and invalidates every panel. The operator account
  model fixes this and is not built.
- **History does not survive a restart either.** The twin is in memory; it
  re-reads the house from Home Assistant in seconds, but yesterday's energy
  readings are gone. Automations, scenes and goals are re-read from disk and are
  not lost.
- **`SYLTRA_ENVIRONMENT=development` blocks every life-safety actuator** —
  valves, breakers, sirens. That is the right setting for a bench. Changing it
  is a decision about a real house with real gas in it.
- **It is plain HTTP.** Fine on a wired LAN you own. It is also why a wall panel
  on a tablet cannot install its offline copy — that needs a certificate
  (`docs/GAPS.md` §2.7).
- **Nothing reaches the internet.** No account, no cloud, no remote access. The
  hub answers on your own network only.

---

## 6. When something is wrong

| What you see | What it means |
|---|---|
| `HOME_ASSISTANT_TOKEN is not set` and the service refuses to start | Deliberate. A hub with no way to reach Home Assistant would serve a console showing an empty house, which reads as *you have no devices* rather than *I am not connected*. |
| Console loads, no devices | The Edge Agent is connected but has mapped nothing. Check the log for `unmapped entity` lines: the device is in Home Assistant but has no capability mapping yet. |
| A control is shown but pressing it does nothing | Read the reason on screen. `RECENT_MANUAL_OVERRIDE` means somebody just used the physical switch and §0 rule 5 says they win for a while. |
| Devices drop out at random | The USB 3 interference described above. Move the stick. |
| `journalctl -u syltra-hub` shows a restart loop | The unit restarts every 5 seconds by design. The error is in the lines above the restart. |
