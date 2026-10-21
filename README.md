# EcoVision AI

EcoVision AI is a local smart waste detection and recycling assistant. The
project includes a ready-to-run SQLite demo dashboard and an optional YOLO
training/inference path.

## Phase 1 setup

### 0. Verify Python

Python 3.10 or newer is required. Check whether it is available:

```powershell
python --version
```

If the command is not recognized, install Python from
<https://www.python.org/downloads/>. During installation, enable **Add python.exe
to PATH**, restart the terminal, and run `python --version` again.

### 1. Create and activate a virtual environment

From the project root in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script activation for the current user, run:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate the environment again.

On Ubuntu/Linux, use:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
```

### 3. Create local configuration

```powershell
Copy-Item .env.example .env
```

The `.env` file is local-only and must not be committed. Phase 1 uses:

- `API_HOST=127.0.0.1`
- `API_PORT=8000`

### 4. Start the API

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Expected startup output includes:

```text
Application startup complete.
Uvicorn running on http://127.0.0.1:8000
```

## Test the Phase 1 endpoints

Open these URLs in a browser:

- <http://127.0.0.1:8000> — returns `{"message":"Welcome to EcoVision AI"}`
- <http://127.0.0.1:8000/health> — returns `{"status":"ok"}`
- <http://127.0.0.1:8000/docs> — opens the interactive Swagger API documentation

From PowerShell, the health check can also be run with:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected output:

```text
status
------
ok
```

Stop the development server with `Ctrl+C`.

## Phase 2: dataset and YOLO training

Phase 2 does not include a dataset. Download or prepare a YOLO-format waste
detection dataset yourself and place it under:

```text
ml\datasets\waste\
├── images\train\
├── images\val\
├── labels\train\
└── labels\val\
```

Every image must have a matching YOLO label file. Labels must use these class
IDs, matching [data.yaml](<ml/data.yaml>):

```text
0 plastic
1 paper
2 cardboard
3 glass
4 metal
5 organic
6 e_waste
7 other
```

Install the Phase 2 dependencies after activating `.venv`:

```powershell
python -m pip install -r backend\requirements.txt
```

Validate the dataset configuration and folders without training:

```powershell
python -m ml.train
```

This command intentionally stops with a clear missing-folder message until the
dataset is placed at `ml\datasets\waste`. After the dataset is available, train
the model:

```powershell
python -m ml.train --epochs 50 --imgsz 640
```

The first run downloads the selected pretrained YOLO base model. Training
results are written to `ml\models\runs\waste_detector`, and the best checkpoint
is copied to:

```text
ml\models\waste_detector.pt
```

Validate the trained model:

```powershell
python -m ml.test
```

The validation command prints mAP50 and mAP50-95 metrics. Do not treat a model
as production-ready without reviewing those metrics and sample predictions.

## Next phase

## Ready-to-run dashboard

The complete local demo works without a dataset or trained model. It uses the
same recommendation and history APIs that a real detector will use.

After installing dependencies and creating `.env`, start the backend:

```powershell
python -m uvicorn backend.app.main:app --reload --host 127.0.0.1 --port 8000
```

Open the dashboard at <http://127.0.0.1:8000/app>. Select a waste type and
confidence, then click **Simulate detection**. The app stores detections in
`data\ecovision.db` and displays history and statistics. The API is also
available at <http://127.0.0.1:8000/docs>.

The dashboard also has a **Start camera** button for a browser webcam preview.
The preview requires browser camera permission. It does not claim to perform
AI inference unless `ml\models\waste_detector.pt` exists.

For standalone real-model webcam inference, install dependencies and run:

```powershell
python -m ml.realtime_detection --model ml\models\waste_detector.pt
```

Press `Q` to close the OpenCV window. The script reports missing models,
unavailable cameras, invalid frames, and always releases the camera on exit.

Useful API calls:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/statistics
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/detect -ContentType "application/json" -Body '{"waste_type":"plastic","confidence":0.92}'
```

The optional real-model path is still available once a compatible model is
provided at `ml\models\waste_detector.pt`. The dashboard demo does not pretend
that a model exists; it explicitly labels simulated detections.
