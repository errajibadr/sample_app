# HTML template avec un peu de JavaScript
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Click Logger</title>
    <style>
        button { margin: 10px; padding: 10px; }
        table { margin-top: 20px; border-collapse: collapse; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            max-width: 300px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .card-title {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        .card-content {
            font-size: 1.2em;
            color: #333;
        }
        .no-clicks {
            color: #999;
            font-style: italic;
        }
    </style>
</head>
<body>
    <h1>Click Logger</h1>
    <button onclick="logClick('Mbappe')">Mbappe</button>
    <button onclick="logClick('Neymar')">Neymar</button>
    <button onclick="logClick('Messi')">Messi</button>

    <div class="card">
        <div class="card-title">Dernier clic</div>
        <div id="last-click" class="card-content">
            <span class="no-clicks">Aucun clic enregistré</span>
        </div>
    </div>

    <h2>Stats:</h2>
    <table id="stats">
        <thead>
            <tr>
                <th>Player</th>
                <th>Total Votes</th>
            </tr>
        </thead>
        <tbody>
        </tbody>
    </table>

    <h2>Most Recent Vote:</h2>
    <div id="clicks"></div>

    <script>
        function logClick(buttonId) {
            fetch('/log-click/' + buttonId, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    loadClicks();
                    loadStats();
                });
        }

        function loadClicks() {
            fetch('/clicks')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('clicks').innerHTML = 
                        data.map(click => `${click.button_id} clicked at ${click.clicked_at}`).join('<br>');
                    
                    // Update last click card
                    const lastClickEl = document.getElementById('last-click');
                    if (data.length > 0) {
                        const lastClick = data[0];
                        lastClickEl.innerHTML = `
                            <strong>${lastClick.button_id}</strong><br>
                            ${lastClick.clicked_at}
                        `;
                    } else {
                        lastClickEl.innerHTML = '<span class="no-clicks">Aucun clic enregistré</span>';
                    }
                });
        }

        function loadStats() {
            fetch('/stats')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.querySelector('#stats tbody');
                    tbody.innerHTML = data.map(stat => 
                        `<tr><td>${stat.button_id}</td><td>${stat.count}</td></tr>`
                    ).join('');
                });
        }

        loadClicks();
        loadStats();
    </script>
</body>
</html>
"""
