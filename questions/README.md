# IoT question banks

151 original open-answer questions based on slide packs 2–5 from the IoT course
(A.A. 2025–2026). The source PDFs are referenced by filename and PDF page number;
they are not included in this repository.

| Bank | Questions | Coverage |
| --- | ---: | --- |
| [02 · Access protocols](iot_02_access_protocols.json) | 38 | Shared media; static/dynamic allocation; TDMA/FDMA delay and overhead; CDMA correlation; ALOHA throughput, delay and stability; CSMA variants and analysis; CSMA/CD; hidden terminals; CSMA/CA, NAV and backoff |
| [03 · WLAN](iot_03_wlan.json) | 26 | Architecture; radio channel and rate adaptation; BSS/ESS; error probability and fragmentation; DCF/PCF; timing; scanning/association; MAC frames and addresses; mobility; power saving; PHY and 802.11 generations |
| [04 · WPAN](iot_04_wpan.json) | 36 | Classic Bluetooth topology/stack/hopping; BLE discovery, energy and reliability; mesh roles, provisioning, friendship and pub/sub; LE Audio and later features; Zigbee stack/topologies/joining/AODV; coexistence, delay, throughput and energy |
| [05 · IoT](iot_05_iot.json) | 51 | IoT gateways; LPWAN; LoRaWAN and Sigfox; broker architectures; MQTT/QoS/MQTT-SN; CoAP; aggregation and routing trade-offs; flooding, gossiping, SPIN variants, Directed Diffusion, LEACH/XLEACH and PEGASIS |

Every question includes a standalone answer, explanation, grading key points and
source references. Prompts mix mechanism explanations, comparisons, failure
scenarios and calculations with explicit assumptions. They cover the substantive
sections of each deck, rather than assigning one question to every slide.

Read each bank's top-level `notes` for corrections and model limitations. In
particular, the answers distinguish CoAP tokens from Message IDs, correct the
MQTT header description, and qualify historical BLE limitations. Protocol
clarifications cite primary specifications where applicable.

```sh
python3 quiz.py questions/*.json --validate
python3 quiz.py questions/iot_02_access_protocols.json --count 10
```
