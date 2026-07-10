/*
 * Webcam capture for candidate registration.
 * Captures a still frame from the browser's webcam and sends it to the backend
 * as a base64 image, alongside the rest of the registration form data.
 *
 * Expects in the HTML:
 *   <video id="webcam" autoplay></video>
 *   <canvas id="snapshot" style="display:none;"></canvas>
 *   <button id="capture-btn">Capture Photo</button>
 *   <img id="preview" style="display:none;">
 *   <input type="hidden" id="photo_data" name="photo_data">
 */

const video = document.getElementById("webcam");
const canvas = document.getElementById("snapshot");
const captureBtn = document.getElementById("capture-btn");
const preview = document.getElementById("preview");
const photoDataInput = document.getElementById("photo_data");

// Start the webcam stream
navigator.mediaDevices.getUserMedia({ video: true })
  .then((stream) => {
    video.srcObject = stream;
  })
  .catch((err) => {
    alert("Could not access webcam. Please allow camera permission and reload.");
    console.error(err);
  });

// Capture a frame when the button is clicked
captureBtn.addEventListener("click", () => {
  const context = canvas.getContext("2d");
  canvas.width = video.videoWidth;
  canvas.height = video.videoHeight;
  context.drawImage(video, 0, 0, canvas.width, canvas.height);

  // Convert captured frame to base64 PNG
  const dataUrl = canvas.toDataURL("image/png");
  photoDataInput.value = dataUrl;

  // Show preview to the candidate
  preview.src = dataUrl;
  preview.style.display = "block";
  video.style.display = "none";
  captureBtn.textContent = "Retake Photo";
});
