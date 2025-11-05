<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Crop Yield Prediction</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <style>
    body {
      background-image: url("https://cdn.pixabay.com/photo/2016/11/29/06/17/agriculture-1867530_1280.jpg");
      background-size: cover;
      background-attachment: fixed;
      background-position: center;
      backdrop-filter: blur(4px);
      color: #222;
      font-family: "Poppins", sans-serif;
    }

    .container {
      background: rgba(255, 255, 255, 0.9);
      border-radius: 20px;
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
      margin-top: 50px;
      padding: 40px;
    }

    h1 {
      font-weight: 700;
      text-align: center;
      color: #2c7a3f;
      margin-bottom: 30px;
    }

    .btn-success {
      background-color: #28a745;
      border: none;
      font-size: 1.1rem;
      border-radius: 10px;
    }

    .btn-success:hover {
      background-color: #218838;
    }

    canvas {
      background: white;
      border-radius: 15px;
      padding: 15px;
      margin-top: 20px;
      box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }
  </style>
</head>

<body>
  <div class="container">
    <h1>🌾 Crop Yield Prediction Dashboard</h1>

    <!-- Input Form -->
    <div class="card p-4 mb-4">
      <h4 class="text-center text-primary mb-3">Input Crop and Climate Features</h4>

      <!-- ✅ AJAX form -->
      <form id="predictForm">
        <div class="row mb-3">
          <div class="col">
            <label><b>Year</b></label>
            <input type="number" class="form-control" name="Year" min="1990" max="2025"
              value="{{ selected_year if selected_year else 2023 }}">
          </div>
          <div class="col">
            <label><b>Average Rainfall (mm/year)</b></label>
            <input type="number" class="form-control" id="rainfall" name="average_rain_fall_mm_per_year" step="any">
          </div>
        </div>

        <div class="row mb-3">
          <div class="col">
            <label><b>Pesticides (tonnes)</b></label>
            <input type="number" class="form-control" name="pesticides_tonnes" step="any">
          </div>
          <div class="col">
            <label><b>Average Temperature (°C)</b></label>
            <input type="number" class="form-control" id="avg_temp" name="avg_temp" step="any">
          </div>
        </div>

        <div class="row mb-3">
          <div class="col">
            <label><b>Area</b></label>
            <select class="form-control" id="areaSelect" name="Area" required>
              <option value="">-- Select Area --</option>
              {% for area in areas %}
              <option value="{{ area }}" {% if selected_area == area %}selected{% endif %}>{{ area }}</option>
              {% endfor %}
            </select>
          </div>
          <div class="col">
            <label><b>Crop (Select Multiple)</b></label>
            <select class="form-control" name="Item" multiple required>
              {% for crop in crops %}
              <option value="{{ crop }}" {% if selected_crops and crop in selected_crops %}selected{% endif %}>{{ crop }}</option>
              {% endfor %}
            </select>
          </div>
        </div>

        <button type="submit" class="btn btn-success btn-lg w-100">🚜 Predict Yield</button>
      </form>
    </div>

    {% if predicted_yield %}
    <div class="result text-center">
      <h3>🌱 Predicted Yield: <b>{{ predicted_yield }} hg/ha</b></h3>
    </div>

    <canvas id="yieldChart"></canvas>
    <script>
      const ctx = document.getElementById('yieldChart').getContext('2d');
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: {{ selected_crops | safe }},
          datasets: [{
            label: 'Predicted Yield (hg/ha)',
            data: {{ predicted_values | safe }},
            borderWidth: 1
          }]
        },
        options: {
          responsive: true,
          scales: {
            y: { beginAtZero: true }
          }
        }
      });
    </script>
    {% endif %}
  </div>

  <!-- 🌤 Weather Auto-fill Script -->
  <script>
    document.getElementById('areaSelect').addEventListener('change', async function () {
      const area = this.value;
      if (!area) return;

      const resp = await fetch(`/get_weather/${area}`);
      const data = await resp.json();

      if (data.avg_temp && data.average_rain_fall_mm_per_year) {
        document.getElementById('avg_temp').value = data.avg_temp;
        document.getElementById('rainfall').value = data.average_rain_fall_mm_per_year;
        alert(`🌤 Live Weather Data Loaded:\nTemp: ${data.avg_temp} °C\nRainfall: ${data.average_rain_fall_mm_per_year} mm/year`);
      } else {
        alert("⚠️ Unable to fetch live weather, using default values.");
      }
    });
  </script>

  <!-- 🚜 AJAX Predict Form -->
  <script>
    document.getElementById("predictForm").addEventListener("submit", async function (e) {
      e.preventDefault();
      const formData = new FormData(this);

      // Optional: loading text or spinner
      const btn = this.querySelector("button");
      const oldText = btn.textContent;
      btn.textContent = "⏳ Predicting...";
      btn.disabled = true;

      const resp = await fetch("/predict", { method: "POST", body: formData });
      const html = await resp.text();

      document.body.innerHTML = html;

      // re-run all scripts (Chart.js, etc.)
      const scripts = document.body.querySelectorAll("script");
      scripts.forEach(oldScript => {
        const newScript = document.createElement("script");
        if (oldScript.src) newScript.src = oldScript.src;
        else newScript.textContent = oldScript.textContent;
        document.body.appendChild(newScript);
      });

      btn.textContent = oldText;
      btn.disabled = false;
    });
  </script>
</body>
</html>
