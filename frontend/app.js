const typeNames = { e_waste: "E-waste" };
const title = value => typeNames[value] || value[0].toUpperCase() + value.slice(1);
const request = (url, options) => fetch(url, options).then(async response => {
  if (!response.ok) throw new Error((await response.json()).detail || "Request failed");
  return response.json();
});

async function refresh() {
  const [stats, history] = await Promise.all([request("/statistics"), request("/detections?limit=10")]);
  document.querySelector("#total").textContent = stats.total_detections;
  document.querySelector("#today").textContent = stats.today_detections;
  const entries = Object.entries(stats.distribution);
  const max = Math.max(1, ...entries.map(([, count]) => count));
  document.querySelector("#distribution").innerHTML = entries.map(([name, count]) =>
    `<div class="bar" style="height:${Math.max(8, count / max * 52)}px"><label>${title(name)}</label></div>`).join("");
  document.querySelector("#history").innerHTML = history.map(item =>
    `<tr><td>${title(item.waste_type)}</td><td>${(item.confidence * 100).toFixed(0)}%</td><td>${item.category}</td><td>${item.recommended_bin}</td><td>${new Date(item.timestamp).toLocaleTimeString()}</td></tr>`).join("");
}

async function loadMode() {
  const status = await request("/model/status");
  document.querySelector("#mode").textContent = status.model_available ? "● YOLO model available" : "● Demo mode";
}

let cameraStream;
document.querySelector("#startCamera").addEventListener("click", async () => {
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({ video: true });
    document.querySelector("#camera").srcObject = cameraStream;
    document.querySelector("#cameraMessage").textContent = "Camera preview active";
    document.querySelector("#cameraIcon").hidden = true;
  } catch (error) {
    document.querySelector("#cameraMessage").textContent = "Camera unavailable: " + error.message;
  }
});
document.querySelector("#stopCamera").addEventListener("click", () => {
  cameraStream?.getTracks().forEach(track => track.stop());
  document.querySelector("#camera").srcObject = null;
  document.querySelector("#cameraMessage").textContent = "Camera is off";
  document.querySelector("#cameraIcon").hidden = false;
});
document.querySelector("#detect").addEventListener("click", async () => {
  const waste_type = document.querySelector("#wasteType").value;
  const confidence = Number(document.querySelector("#confidence").value);
  try {
    const item = await request("/detect", { method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({ waste_type, confidence }) });
    document.querySelector("#result").innerHTML = `<span class="badge">${item.category}</span><h3>${title(item.waste_type)}</h3><p>Confidence: ${(item.confidence * 100).toFixed(0)}%</p><div class="recommendation"><strong>${item.recommended_bin}</strong><p>${item.recommendation_message}</p></div>`;
    await refresh();
  } catch (error) { document.querySelector("#result").innerHTML = `<p class="muted">${error.message}</p>`; }
});
document.querySelector("#refresh").addEventListener("click", refresh);
Promise.all([refresh(), loadMode()]).catch(error => document.querySelector("#result").innerHTML = `<p class="muted">${error.message}</p>`);
