# Audio and video foundation

The isolated Toolbox image includes Faster-Whisper, FFmpeg, ffprobe, Tesseract,
OpenCV, and PySceneDetect. It has no outbound network and no model is downloaded
at runtime.

## Approved reproducible Whisper choice

Use `Systran/faster-whisper-small` converted CTranslate2 files, staged by an
administrator into the Toolbox's dedicated `i3s-file-service-data` volume at
`/data/models/faster-whisper-small`. This is approximately 0.5 GB on disk. Run
on CPU using `WHISPER_DEVICE=cpu` and `WHISPER_COMPUTE_TYPE=int8`; expect roughly
1-2 GB host RAM during a short transcription and no A100/P100 VRAM use. It is a
useful English/Portuguese baseline without competing with generation or embeddings.

The service only enables `transcribe_audio` after `WHISPER_MODEL_PATH` names a
directory below `/data`. No model is provisioned in this run: root has only 15
GiB free and a model blob must not be put in the migration archive.

## Vision assessment

Qwen3-VL 4B is the preferred evaluation class, with a 4-bit quantization expected
to require roughly 3-5 GB model storage and 4-6 GB VRAM plus image context. It is
technically suitable for selected keyframes, but should be on-demand on the A100;
it must never share the P100 embedding service. No vision backend was pulled or
kept resident, so `analyze_video` reports metadata only. A later deployment should
verify the exact Ollama model tag and load/unload behavior before enabling it.

## Video flow

`inspect_video` uses ffprobe. `extract_keyframes` emits a representative I-frame;
`transcribe_video` reuses audio transcription when the approved model is staged.
Do not submit every frame to a model: extract scene/keyframe samples, OCR only
useful frames, then provide the resulting timeline and transcript to qwen3.5.
