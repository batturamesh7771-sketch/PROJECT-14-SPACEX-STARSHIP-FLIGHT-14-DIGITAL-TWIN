/**
 * Phase 10: Virtualized Data Explorer & Ledger Inspector
 * Starship Flight 14 Digital Engineering Lab
 *
 * Implements:
 *   - Virtualized pagination of 10,000+ data samples across all 9 phases
 *   - Real-time debounced search & phase filtering
 *   - Client-side CSV export
 *   - Planned vs Observed Event Diff Ledger
 */

class DataExplorerManager {
  constructor(records, comparisonEvents, runManifest) {
    this.allRecords = records || [];
    this.filteredRecords = [...this.allRecords];
    this.comparisonEvents = comparisonEvents || [];
    this.runManifest = runManifest || {};

    this.pageSize = 50;
    this.currentPage = 1;

    this.initLedgerTable();
    this.initExplorer();
    this.initManifestTab();
  }

  initLedgerTable() {
    const tbody = document.getElementById("ledger-tbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    this.comparisonEvents.forEach(ev => {
      const tr = document.createElement("tr");

      const pTimeStr = ev.planned_time_s !== null ? `T+${ev.planned_time_s.toFixed(1)}s` : "N/A";
      const aTimeStr = ev.actual_time_s !== null ? `T+${ev.actual_time_s.toFixed(1)}s` : "N/A";
      const deltaStr = ev.delta_s !== null ? `${ev.delta_s > 0 ? "+" : ""}${ev.delta_s.toFixed(1)}s` : "—";

      let statusClass = "confirmed";
      if (ev.status === "NOT EXECUTED") statusClass = "not-executed";
      if (ev.status.includes("ANOMALY")) statusClass = "anomaly";

      tr.innerHTML = `
        <td><strong>${ev.event}</strong></td>
        <td>${pTimeStr}</td>
        <td>${aTimeStr}</td>
        <td>${deltaStr}</td>
        <td><span class="status-tag ${statusClass}">${ev.status}</span></td>
        <td style="color: var(--text-muted); font-size: 10px;">${ev.description}</td>
      `;
      tbody.appendChild(tr);
    });
  }

  initExplorer() {
    const searchInput = document.getElementById("explorer-search");
    const phaseFilter = document.getElementById("explorer-phase-filter");
    const exportBtn = document.getElementById("btn-export-csv");
    const prevBtn = document.getElementById("explorer-prev");
    const nextBtn = document.getElementById("explorer-next");

    if (searchInput) {
      let timeout = null;
      searchInput.addEventListener("input", (e) => {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
          this.applyFilters(e.target.value, phaseFilter ? phaseFilter.value : "ALL");
        }, 150);
      });
    }

    if (phaseFilter) {
      phaseFilter.addEventListener("change", (e) => {
        this.applyFilters(searchInput ? searchInput.value : "", e.target.value);
      });
    }

    if (prevBtn) {
      prevBtn.addEventListener("click", () => {
        if (this.currentPage > 1) {
          this.currentPage--;
          this.renderExplorerPage();
        }
      });
    }

    if (nextBtn) {
      nextBtn.addEventListener("click", () => {
        const maxPage = Math.ceil(this.filteredRecords.length / this.pageSize);
        if (this.currentPage < maxPage) {
          this.currentPage++;
          this.renderExplorerPage();
        }
      });
    }

    if (exportBtn) {
      exportBtn.addEventListener("click", () => this.exportCurrentCSV());
    }

    this.renderExplorerPage();
  }

  applyFilters(query, phase) {
    const q = (query || "").toLowerCase().trim();
    this.filteredRecords = this.allRecords.filter(r => {
      const matchPhase = phase === "ALL" || r.phase === phase || r.source.includes(phase);
      if (!matchPhase) return false;
      if (!q) return true;
      return (
        String(r.id).includes(q) ||
        String(r.source).toLowerCase().includes(q) ||
        String(r.time_s).includes(q) ||
        String(r.phase).toLowerCase().includes(q)
      );
    });

    this.currentPage = 1;
    this.renderExplorerPage();
  }

  renderExplorerPage() {
    const tbody = document.getElementById("explorer-tbody");
    const infoEl = document.getElementById("explorer-page-info");
    if (!tbody) return;

    tbody.innerHTML = "";
    const total = this.filteredRecords.length;
    const maxPage = Math.max(1, Math.ceil(total / this.pageSize));
    const startIdx = (this.currentPage - 1) * this.pageSize;
    const endIdx = Math.min(startIdx + this.pageSize, total);

    if (infoEl) {
      infoEl.innerText = `Showing records ${startIdx + 1}–${endIdx} of ${total} (Page ${this.currentPage} / ${maxPage})`;
    }

    for (let i = startIdx; i < endIdx; i++) {
      const r = this.filteredRecords[i];
      const tr = document.createElement("tr");

      tr.innerHTML = `
        <td>${r.id}</td>
        <td><span class="card-badge">${r.source}</span></td>
        <td>${r.phase}</td>
        <td>${r.time_s !== null ? r.time_s.toFixed(2) : "—"}</td>
        <td>${r.altitude_km !== undefined && r.altitude_km !== null ? r.altitude_km.toFixed(2) : "—"}</td>
        <td>${r.velocity_m_s !== undefined && r.velocity_m_s !== null ? r.velocity_m_s.toFixed(1) : (r.speed_km_s ? (r.speed_km_s * 1000).toFixed(1) : "—")}</td>
        <td>${r.mach !== undefined && r.mach !== null ? r.mach.toFixed(2) : "—"}</td>
        <td>${r.apparent_g !== undefined && r.apparent_g !== null ? r.apparent_g.toFixed(2) : (r.accel_g !== undefined ? r.accel_g.toFixed(2) : "—")}</td>
        <td>${r.thrust_mn !== undefined && r.thrust_mn !== null ? r.thrust_mn.toFixed(2) : "—"}</td>
        <td>${r.heat_flux_mw_m2 !== undefined && r.heat_flux_mw_m2 !== null ? r.heat_flux_mw_m2.toFixed(3) : "—"}</td>
      `;
      tbody.appendChild(tr);
    }
  }

  exportCurrentCSV() {
    if (!this.filteredRecords || this.filteredRecords.length === 0) return;
    const keys = Object.keys(this.filteredRecords[0]);
    let csvContent = keys.join(",") + "\n";

    this.filteredRecords.forEach(r => {
      const row = keys.map(k => {
        const val = r[k];
        if (val === null || val === undefined) return "";
        return String(val).replace(/,/g, ";");
      });
      csvContent += row.join(",") + "\n";
    });

    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `starship_flight14_telemetry_export_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }

  initManifestTab() {
    const pre = document.getElementById("manifest-json-pre");
    if (pre && this.runManifest) {
      pre.innerText = JSON.stringify(this.runManifest, null, 2);
    }
  }
}

window.DataExplorerManager = DataExplorerManager;
