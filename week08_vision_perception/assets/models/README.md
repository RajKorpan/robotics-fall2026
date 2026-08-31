# Instructor-provided learned model

Place the course's frozen COCO ONNX detector at `detector.onnx`. The matching `labels.txt` is committed with the lab; the model binary is intentionally not committed to Git.

The supplied node accepts Ultralytics-style YOLO ONNX output shaped as `[1, classes+4, candidates]` or `[1, candidates, classes+4]`. Freeze the exact model, labels, input size, license, source URL, and SHA-256 checksum before distributing the course image. Students do not train or replace the model during the lab.

Grading must also include the supplied recorded condition run so a model download, GPU, or network service is never required.
