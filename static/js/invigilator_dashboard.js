// ==========================================
// Invigilator Dashboard
// Online Exam Monitoring Platform
// ==========================================

document.addEventListener("DOMContentLoaded", () => {

    const examSelect = document.getElementById("exam-select");
    const cohortSummary = document.getElementById("cohort-summary");
    const tableBody = document.querySelector("#candidates-table tbody");
    const eventsBody = document.querySelector("#events-table tbody");
    const kpiTotal = document.getElementById("kpi-total");
    const kpiHigh = document.getElementById("kpi-high");
    const kpiMedium = document.getElementById("kpi-medium");
    const kpiLow = document.getElementById("kpi-low");
    const kpiEvents = document.getElementById("kpi-events");

    let distributionChart = null;
    let clusterChart = null;

    function riskClass(label) {
        if (label === "Low") return "risk-low";
        if (label === "Medium") return "risk-medium";
        if (label === "High") return "risk-high";
        return "risk-unknown";
    }

    function severityClass(sev) {
        const s = (sev || "").toLowerCase();
        if (s === "high") return "risk-high";
        if (s === "medium") return "risk-medium";
        if (s === "low") return "risk-low";
        return "risk-unknown";
    }

    function formatEventType(type) {
        if (!type) return "Unknown";
        return type.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
    }

    function formatTime(iso) {
        if (!iso) return "—";
        const d = new Date(iso);
        if (isNaN(d.getTime())) return iso;
        return d.toLocaleString();
    }

    async function fetchJSON(url) {
        const resp = await fetch(url);
        if (!resp.ok) {
            throw new Error(`Request to ${url} failed with status ${resp.status}`);
        }
        return resp.json();
    }


    async function loadExams() {
        try {
            const data = await fetchJSON("/api/analytics/exams");
            examSelect.innerHTML = "";
            if (!data.exams || data.exams.length === 0) {
                examSelect.innerHTML = '<option value="">No exams found</option>';
                return;
            }
            data.exams.forEach(exam => {
                const opt = document.createElement("option");
                opt.value = exam.id;
                opt.textContent = `${exam.title} (#${exam.id})`;
                examSelect.appendChild(opt);
            });
            loadExamData(examSelect.value);
        } catch (err) {
            examSelect.innerHTML = '<option value="">Failed to load exams</option>';
            console.error(err);
        }
    }

    function renderDistributionChart(dist) {
        const ctx = document.getElementById("distribution-chart");
        const labels = dist.histogram.bin_edges.slice(0, -1).map((edge, i) =>
            `${Math.round(edge)}-${Math.round(dist.histogram.bin_edges[i + 1])}`
        );

        if (distributionChart) {
            distributionChart.destroy();
        }
        distributionChart = new Chart(ctx, {
            type: "bar",
            data: {
                labels,
                datasets: [{
                    label: "Candidates",
                    data: dist.histogram.counts,
                    backgroundColor: "#ff5a36"
                }]
            },
            options: {
                responsive: true,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
            }
        });
    }

    function renderHeatmap(heatmap) {
        const container = document.getElementById("heatmap-container");
        if (!heatmap.candidate_ids || heatmap.candidate_ids.length === 0) {
            container.innerHTML = "<p>No event data for this cohort yet.</p>";
            return;
        }

        let html = "<table><thead><tr><th>Candidate</th>";
        heatmap.event_types.forEach(et => { html += `<th>${et}</th>`; });
        html += "</tr></thead><tbody>";

        heatmap.candidate_ids.forEach((cid, i) => {
            html += `<tr><td>#${cid}</td>`;
            heatmap.matrix[i].forEach(count => { html += `<td>${count}</td>`; });
            html += "</tr>";
        });
        html += "</tbody></table>";
        container.innerHTML = html;
    }

    function renderClusterChart(clusters) {
        const ctx = document.getElementById("cluster-chart");
        const colorForRisk = { "Low": "#16a34a", "Medium": "#d97706", "High": "#dc2626", "Insufficient Data": "#6b7280" };

        const points = clusters.assignments.map(a => ({
            x: a.candidate_id,
            y: a.integrity_score
        }));
        const colors = clusters.assignments.map(a => colorForRisk[a.cluster_risk_label] || "#6b7280");
        const labels = clusters.assignments.map(a => a.cluster_risk_label || "Insufficient Data");

        if (clusterChart) {
            clusterChart.destroy();
        }
        clusterChart = new Chart(ctx, {
            type: "scatter",
            data: {
                datasets: [{
                    label: "Candidates",
                    data: points,
                    backgroundColor: colors,
                    pointRadius: 6
                }]
            },
            options: {
                responsive: true,
                scales: {
                    x: { title: { display: true, text: "Candidate ID" } },
                    y: { title: { display: true, text: "Integrity Score" }, min: 0, max: 100 }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (item) => `Candidate #${item.raw.x} — ${labels[item.dataIndex]} risk, score ${item.raw.y}`
                        }
                    }
                }
            }
        });
    }

    function renderTable(clusters, examId) {
        tableBody.innerHTML = "";
        clusters.assignments.forEach(a => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>#${a.candidate_id}</td>
                <td>${a.integrity_score}</td>
                <td><span class="risk-badge ${riskClass(a.risk_label)}">${a.risk_label}</span></td>
                <td><span class="risk-badge ${riskClass(a.cluster_risk_label)}">${a.cluster_risk_label}</span></td>
                <td><span class="status-pill">Monitored</span></td>
                <td><a class="table-action" href="/api/export/${a.candidate_id}/${examId}?format=csv">Export CSV</a></td>
            `;
            tableBody.appendChild(tr);
        });
    }

    function renderKPIs(clusters, eventCount) {
        const assignments = clusters.assignments || [];
        kpiTotal.textContent = clusters.cohort_size ?? assignments.length;
        kpiHigh.textContent = assignments.filter(a => a.cluster_risk_label === "High").length;
        kpiMedium.textContent = assignments.filter(a => a.cluster_risk_label === "Medium").length;
        kpiLow.textContent = assignments.filter(a => a.cluster_risk_label === "Low").length;
        kpiEvents.textContent = eventCount;
    }

    function renderEvents(flags) {
        eventsBody.innerHTML = "";
        if (!flags || flags.length === 0) {
            eventsBody.innerHTML = '<tr><td colspan="4" class="invig-empty-row">No integrity events recorded for this exam.</td></tr>';
            return;
        }
        // flags_storage returns ascending by created_at; show most recent first.
        const recent = [...flags].reverse().slice(0, 15);
        recent.forEach(f => {
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>#${f.candidate_id}</td>
                <td>${formatEventType(f.flag_type)}</td>
                <td>${formatTime(f.created_at)}</td>
                <td><span class="risk-badge ${severityClass(f.severity)}">${f.severity || "unknown"}</span></td>
            `;
            eventsBody.appendChild(tr);
        });
    }

    async function loadExamData(examId) {
        if (!examId) return;

        cohortSummary.textContent = "Loading...";

        try {
            const [dist, heatmap, clusters, flagsResult] = await Promise.all([
                fetchJSON(`/api/analytics/distribution/${examId}`),
                fetchJSON(`/api/analytics/heatmap/${examId}`),
                fetchJSON(`/api/analytics/clusters/${examId}`),
                fetchJSON(`/api/flags?exam_id=${examId}`)
            ]);

            cohortSummary.textContent = `Cohort size: ${dist.cohort_size}`;
            renderDistributionChart(dist);
            renderHeatmap(heatmap);
            renderClusterChart(clusters);
            renderTable(clusters, examId);
            renderKPIs(clusters, flagsResult.count ?? (flagsResult.flags || []).length);
            renderEvents(flagsResult.flags);
        } catch (err) {
            cohortSummary.textContent = "Failed to load exam data.";
            console.error(err);
        }
    }

    examSelect.addEventListener("change", (e) => loadExamData(e.target.value));

    loadExams();

});
