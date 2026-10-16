# Worker processing pipeline

Snapshot verified on Core-Backend `15fbad106` (master + PR #1107) and `develop` `be83fd218`, 2026-10. **Check it against the code under test before relying on it** (`scripts/check_pipeline.py`). Code moves; this file is a map, not the territory.

## Contents
1. Threads
2. Processing bin element order
3. Batches, N and S
4. Muxer batch buffers
5. Python coupling between threads
6. What decides the pace

## 1. Threads

Every `queue` element starts a new streaming thread. A frame passes these threads in order:

| Thread | Scope | Elements | Notes |
|---|---|---|---|
| T1 source | per camera | camera src → imgstabilisation | Jenoptik / Basler source bins |
| T3 prerecording | per camera | metadata → shmsink | side branch for recordings |
| T2 pre-mux | per camera | `queue_source_<cam>_processing` → typefind → videodeblur (cond.) → nvvideoconvert (cond.) | the queue is **leaky, max 1 buffer**: frames the muxer does not take in time are dropped here |
| T4 muxer | shared | `nvstreammux` → capsfilter → `queue_processing` | builds one batch = one frame per camera |
| **T5 stage 1** | shared | `batch_validation` → `inference` → `queue_inference` | master: Python `inference_py.py`; develop: C++ `inferencecpp` |
| **T6 stage 2** | shared, serial | ~20 plugins (list below) → `nvstreamdemux` | handles **every** batch |
| T7… | per camera | `queue_src_<n>` → affinetransformation → tee → drawn (nvdsosd) / raw → input-selectors → WebRTC / RTSP / HTTP encoding bins | streams come **after** stage 2; the encoding bin can add `videorate` to a fixed fps |
| Panorama | optional | own thread | |

Live Watchkeeper cameras deliver **12 fps** (encoder caps show `framerate=12/1`). `source_videorate_fps` in `parameters.json` (14 on Watchkeeper 1024S) is for file replay, not live.

## 2. Processing bin element order

From `Core/Gst/plugins/python/processing_bin.py`, `elements = [...]`. Language per element from the team's pipeline diagram (C++ = purple, Python = orange):

- **T4:** nvstreammux, capsfilter, queue_processing
- **T5:** batch_validation (Py), inference (Py on master / C++ `inferencecpp` on develop), queue_inference
- **T6:** ignoremaskfilter (C++), cpptransformation (C++), sensorfusion (C++), horizon_detection (Py), applystabilisation (C++), detectionhorizonfilter (C++), cppdistanceestimation (C++), imgtracker (C++), radar_fusion (Py), trajectoryclassification (Py), object_relabeller (Py), threatlevelmanager (C++), alarmmanager (C++), postprocessing (C++), track_object (Py, conditional), wsminiimages (C++, conditional), metadatacache (C++), alertsocket (Py), wsstatus (C++), then nvstreamdemux

`alertsocket` (extended API alert feed) copies the master camera image to the CPU and JPEG-encodes it **at full resolution on every batch**, and walks the object metadata three times. It only runs when the extended API is active (`POWER_Const/interface_activated` or an `EXTENDED_API` license); since PR #1107 also only when its `enabled` property is true (default false, nothing sets it).

## 3. Batches, N and S

`processing_interval` (profile `parameters.json`; Watchkeeper 1024S = 1) is the number of batches the network skips between runs. With 1, batches alternate:

- **N**: the network runs. Stage 1 does the real work (image copy, network, objects/metadata).
- **S**: the network is skipped. Stage 1 passes the batch in about 1 ms.

Stage 2 runs on **every** batch, N and S. So always compare the stages **per cycle** (interval + 1 batches), not per batch: a stage-2 element that is shorter than inference per batch can still be the bottleneck because it runs twice as often.

Rates to keep apart:
- **worker fps** = batches through stage 2 per second (wsstatus output), max = camera fps.
- **network runs per second** = processing fps, max = camera fps / (interval + 1) = 6.
- **stream fps** = camera rate (12); gst-shark's per-second framerate counter reads ~13.

## 4. Muxer batch buffers

`processing_bin.py` `_configure()` sets `buffer-pool-size` **4** when `USE_NEW_NVSTREAMMUX != "yes"`; `Core/WorkerProfiles/common.env` sets it to `"no"` (legacy muxer). So at most 4 batches exist between the muxer and the end of stage 2. When stage 2 is slow, batches queue in front of it, hold all 4 buffers, the muxer cannot build new batches, stage 1 idles (queue_processing empty) and the leaky T2 queues drop camera frames. A bigger pool would move the waiting, not remove it: the slowest stage still sets the rate. The team questioned the pool size; if it matters, test with a bigger pool or the new muxer.

## 5. Python coupling between threads

T5 and T6 are separate threads, but on master both contain Python elements, so they share the GIL and the CPU cores. A Python element in T6 (alertsocket) slows the CPU-side steps of Python inference in T5 (image copy, object handling), while the GPU network call barely changes. On develop, T5 uses C++ `inferencecpp`, which removes T5 from most of that coupling.

## 6. What decides the pace

The steady-state rate is set by the slowest of: camera (cycle = (interval+1) × 83 ms at 12 fps), T5 per cycle, T6 per cycle. Queue fill levels show which one:
- `queue_processing` holds batches, `queue_inference` empty → T5 (inference) is the bottleneck.
- `queue_inference` holds batches, `queue_processing` empty → T6 is the bottleneck (and the muxer pool runs dry).
- both empty, stage 1 waits a little before each N → camera-bound, nothing in the worker limits it.
