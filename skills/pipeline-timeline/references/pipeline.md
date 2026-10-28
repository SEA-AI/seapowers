# How the worker pipeline behaves

The concepts below are stable; the details (which elements, which thread, which interval) change with the code. Read the current details from the Core-Backend commit installed on the device (`git show <commit>:<path>`), not from memory.

## Where to read it

| Question | Where |
|---|---|
| Elements of the processing bin and their order | `Core/Gst/plugins/python/processing_bin.py`, the `elements = [...]` list and the conditional inserts below it |
| Streams after the processing bin (demux, encoders, recordings) | `Worker/pipeline.py` |
| Python or C++ element | Python elements live in `Core/Gst/plugins/python/`, C++ elements in `Core/Gst/plugins/c_plugins/` |
| Which inference element runs | the `("inference…", "inference")` entry in `processing_bin.py` |
| How often the network runs | `processing_interval` in the product's `Core/WorkerProfiles/<product>/<profile>/parameters.json` |
| Replay frame rate | `source_videorate_fps` in the same file (live cameras deliver their own rate) |
| Muxer batch buffers | `buffer-pool-size` in `processing_bin.py` (`_configure`) and `USE_NEW_NVSTREAMMUX` in `Core/WorkerProfiles/common.env` |
| Switch of the element under test | its GObject properties and the first lines of its `do_transform_ip` |
| What the perf script traces | the `PERF_TRACERS` default in `Tools/scripts/power_mode_perf.sh` |

Devices often run test patches on top of the installed commit. A run's log shows what really ran (`Using model:`, `Loaded scenario`, extended API state); trust the run over the commit.

## Threads

Every `queue` element starts a new streaming thread. Read the element list and cut it at each `queue`: the elements between two queues run one after another in one thread. Threads run in parallel across batches, never within one batch. The slowest thread sets the rate of the whole pipeline.

The two threads that usually matter:
- **Stage 1**: from the queue after the muxer to the queue after inference (inference and what sits next to it).
- **Stage 2**: everything after the inference queue up to the demuxer (tracking, distance, alarms, websocket output). It handles **every** batch.

Queues in front of the muxer can be leaky: frames the muxer does not take in time are dropped there, not queued.

## Batches, N and S

`processing_interval` is the number of batches the network skips between runs. With 1, batches alternate:
- **N**: the network runs, stage 1 does the real work.
- **S**: the network is skipped, stage 1 passes the batch in about a millisecond.

Stage 2 runs on N and S. Compare the stages **per cycle** (interval + 1 batches), not per batch: a stage-2 element shorter than inference can still be the bottleneck because it runs more often.

Rates to keep apart:
- **Worker fps**: batches through stage 2 per second (`wsstatus` output), at most the camera rate.
- **Network runs per second** (processing fps): at most camera rate / (interval + 1).
- **Stream fps**: the camera rate the encoders see.

## Muxer batch buffers

The muxer can only build a batch while it has a free batch buffer. When a later stage is slow, batches pile up in front of it, hold all buffers, the muxer stops, the stages before the slow one idle and the leaky queues drop camera frames. A bigger pool moves the waiting, it does not remove it.

## Python coupling

Two threads with Python elements share the GIL and the CPU cores. A slow Python element in stage 2 also slows the CPU-side steps of a Python inference element in stage 1 (image copy, object handling), while the GPU call barely changes. A C++ inference element removes most of that coupling.

## What sets the pace

The rate is set by the slowest of: the camera, stage 1 per cycle, stage 2 per cycle. The queue fill levels show which:
- the queue in front of inference holds batches, the one after it is empty: **inference** is the bottleneck;
- the queue after inference holds batches, the one in front is empty: **stage 2** is the bottleneck (and the muxer pool runs dry);
- both empty and stage 1 waits a little before each N batch: **camera-bound**, nothing in the worker limits it.
