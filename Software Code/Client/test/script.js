const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const ctx = canvas.getContext("2d");

// Start webcam
navigator.mediaDevices.getUserMedia({ video: true }).then(stream => {
  video.srcObject = stream;
});

// Send frame every 200ms
setInterval(async () => {
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

  canvas.toBlob(async (blob) => {
    const form = new FormData();
    form.append("frame", blob, "frame.jpg");

    const res = await fetch("http://127.0.0.1:8000/detect/live_frame", {
      method: "POST",
      body: form,
    });

    const json = await res.json();
    drawDetections(json.detections);
  }, "image/jpeg");
}, 200);


// Draw boxes on canvas
function drawDetections(detections) {
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  ctx.lineWidth = 2;
  ctx.font = "18px Arial";

  detections.forEach(det => {
    const [x1, y1, x2, y2] = det.bbox;
    ctx.strokeStyle = "red";
    ctx.fillStyle = "red";
    ctx.strokeRect(x1, y1, x2 - x1, y2 - y1);
    ctx.fillText(`${det.class} (${(det.confidence*100).toFixed(1)}%)`, x1, y1 - 5);
  });
}
