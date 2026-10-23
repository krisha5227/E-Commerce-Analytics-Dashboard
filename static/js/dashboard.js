/**
 * E-Commerce Analytics Dashboard Frontend Controller
 * Powered by Chart.js 4.x and Vanilla JavaScript.
 */

// Utility formatters
const formatCurrency = (val) => {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0
  }).format(val || 0);
};

const formatNumber = (val) => {
  return new Intl.NumberFormat("en-US").format(val || 0);
};

const formatPercent = (val) => {
  return `${(val || 0).toFixed(1)}%`;
};

// Global chart registry to destroy/recreate cleanly
const chartInstances = {};

function renderOrUpdateChart(canvasId, config) {
  if (chartInstances[canvasId]) {
    chartInstances[canvasId].destroy();
  }
  const ctx = document.getElementById(canvasId);
  if (!ctx) return null;
  chartInstances[canvasId] = new Chart(ctx, config);
  return chartInstances[canvasId];
}

// -------------------------------------------------------------
// 1. Overview Dashboard Page
// -------------------------------------------------------------
async function loadOverviewData() {
  const dateFilter = document.getElementById("dateFilter") ? document.getElementById("dateFilter").value : "all";
  let params = new URLSearchParams();

  if (dateFilter === "2025") {
    params.set("start_date", "2025-01-01");
    params.set("end_date", "2025-12-31");
  } else if (dateFilter === "2024") {
    params.set("start_date", "2024-01-01");
    params.set("end_date", "2024-12-31");
  } else if (dateFilter === "last90") {
    params.set("start_date", "2025-10-01");
    params.set("end_date", "2025-12-31");
  } else if (dateFilter === "last30") {
    params.set("start_date", "2025-12-01");
    params.set("end_date", "2025-12-31");
  }

  try {
    const res = await fetch(`/api/overview?${params.toString()}`);
    const data = await res.json();
    updateOverviewKPIs(data.kpis);
    renderSalesTrendChart(data.trend);
    renderCategoryChart(data.categories);
    renderTopProductsChart(data.top_products);
  } catch (err) {
    console.error("Failed to load overview data:", err);
  }
}

function updateOverviewKPIs(kpis) {
  if (!kpis) return;
  const setEl = (id, text) => {
    const el = document.getElementById(id);
    if (el) el.innerText = text;
  };

  setEl("kpiRevenue", formatCurrency(kpis.total_revenue));
  setEl("kpiProfit", formatCurrency(kpis.total_profit));
  setEl("kpiMargin", formatPercent(kpis.profit_margin));
  setEl("kpiAOV", formatCurrency(kpis.aov));
  setEl("kpiOrders", formatNumber(kpis.total_orders));
  setEl("kpiReturningRev", `${formatPercent(kpis.returning_rev_pct)} (${formatCurrency(kpis.returning_revenue)})`);
  setEl("kpiRepeatCust", `${formatPercent(kpis.repeat_customers_pct)} (${formatNumber(kpis.repeat_customers_count)} cust)`);
}

function renderSalesTrendChart(trend) {
  if (!trend || !trend.labels) return;

  renderOrUpdateChart("salesTrendChart", {
    type: "line",
    data: {
      labels: trend.labels,
      datasets: [
        {
          label: "Revenue ($)",
          data: trend.revenue,
          borderColor: "#2563eb",
          backgroundColor: "rgba(37, 99, 235, 0.08)",
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointRadius: 3,
          pointHoverRadius: 6
        },
        {
          label: "Net Profit ($)",
          data: trend.profit,
          borderColor: "#10b981",
          backgroundColor: "rgba(16, 185, 129, 0.06)",
          fill: true,
          tension: 0.35,
          borderWidth: 2,
          pointRadius: 3,
          pointHoverRadius: 6
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: { position: "top", labels: { boxWidth: 12, font: { family: "Inter", size: 12 } } },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`
          }
        }
      },
      scales: {
        x: { grid: { display: false } },
        y: {
          grid: { color: "#f1f5f9" },
          ticks: {
            callback: (val) => "$" + (val >= 1000 ? (val / 1000).toFixed(0) + "k" : val)
          }
        }
      }
    }
  });
}

function renderCategoryChart(categories) {
  if (!categories || !categories.length) return;

  renderOrUpdateChart("categoryChart", {
    type: "doughnut",
    data: {
      labels: categories.map((c) => c.category),
      datasets: [
        {
          data: categories.map((c) => c.revenue),
          backgroundColor: ["#2563eb", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"],
          borderWidth: 2,
          borderColor: "#ffffff"
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "right", labels: { boxWidth: 12, font: { size: 11 } } },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.label}: ${formatCurrency(ctx.raw)}`
          }
        }
      },
      cutout: "68%"
    }
  });
}

function renderTopProductsChart(products) {
  if (!products || !products.length) return;

  renderOrUpdateChart("topProductsChart", {
    type: "bar",
    data: {
      labels: products.map((p) => p.name.length > 22 ? p.name.substring(0, 20) + "…" : p.name),
      datasets: [
        {
          label: "Revenue ($)",
          data: products.map((p) => p.revenue),
          backgroundColor: "#3b82f6",
          borderRadius: 4
        },
        {
          label: "Profit ($)",
          data: products.map((p) => p.profit),
          backgroundColor: "#10b981",
          borderRadius: 4
        }
      ]
    },
    options: {
      indexAxis: "y",
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top", labels: { boxWidth: 12 } },
        tooltip: {
          callbacks: {
            label: (ctx) => ` ${ctx.dataset.label}: ${formatCurrency(ctx.raw)}`
          }
        }
      },
      scales: {
        x: {
          grid: { color: "#f1f5f9" },
          ticks: { callback: (v) => "$" + (v >= 1000 ? (v / 1000).toFixed(0) + "k" : v) }
        },
        y: { grid: { display: false } }
      }
    }
  });
}

// -------------------------------------------------------------
// 2. Customer Analytics Page (RFM, Pareto, Cohort)
// -------------------------------------------------------------
async function loadCustomerAnalytics() {
  try {
    const res = await fetch("/api/customer-analytics");
    const data = await res.json();

    renderParetoChart(data.pareto);
    renderRFMChartAndTable(data.rfm);
    renderCohortMatrix(data.cohorts);
  } catch (err) {
    console.error("Failed to load customer analytics:", err);
  }
}

function renderParetoChart(pareto) {
  if (!pareto || !pareto.deciles) return;

  // Set Top 20% highlight badge
  const top20Badge = document.getElementById("paretoTop20Highlight");
  if (top20Badge) {
    top20Badge.innerText = `Top 20% of customers generate ${pareto.top_20_pct_rev.toFixed(1)}% of total revenue.`;
  }

  const labels = pareto.deciles.map((d) => `Top ${d.customer_pct}%`);
  const values = pareto.deciles.map((d) => d.revenue_pct);

  renderOrUpdateChart("paretoChart", {
    type: "line",
    data: {
      labels: labels,
      datasets: [
        {
          label: "Cumulative Revenue %",
          data: values,
          borderColor: "#8b5cf6",
          backgroundColor: "rgba(139, 92, 246, 0.12)",
          fill: true,
          tension: 0.25,
          borderWidth: 3,
          pointRadius: 5,
          pointBackgroundColor: "#8b5cf6"
        },
        {
          label: "Linear 1:1 Equality",
          data: [10, 20, 30, 40, 50, 60, 70, 80, 90, 100],
          borderColor: "#94a3b8",
          borderDash: [5, 5],
          borderWidth: 1.5,
          pointRadius: 0,
          fill: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: "top" },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ${ctx.raw.toFixed(1)}%`
          }
        }
      },
      scales: {
        y: {
          min: 0,
          max: 100,
          ticks: { callback: (v) => `${v}%` }
        }
      }
    }
  });
}

function renderRFMChartAndTable(rfm) {
  if (!rfm || !rfm.summary) return;

  const segmentLabels = rfm.summary.map((s) => s.segment);
  const revenueValues = rfm.summary.map((s) => s.total_revenue);
  const customerCounts = rfm.summary.map((s) => s.customer_count);

  renderOrUpdateChart("rfmChart", {
    type: "bar",
    data: {
      labels: segmentLabels,
      datasets: [
        {
          label: "Customer Count",
          data: customerCounts,
          backgroundColor: "#3b82f6",
          borderRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: { grid: { display: false } },
        y: { grid: { color: "#f1f5f9" } }
      }
    }
  });

  // Populate Table
  const tableBody = document.getElementById("rfmTableBody");
  if (!tableBody) return;

  const segmentBadges = {
    "Champions": "badge-success",
    "Loyal Customers": "badge-primary",
    "Potential Loyalists": "badge-primary",
    "Promising / New": "badge-neutral",
    "Needs Attention": "badge-warning",
    "At Risk": "badge-warning",
    "Hibernating / Lost": "badge-danger"
  };

  tableBody.innerHTML = rfm.summary
    .map(
      (s) => `
      <tr>
        <td><span class="badge ${segmentBadges[s.segment] || "badge-neutral"}">${s.segment}</span></td>
        <td><strong>${formatNumber(s.customer_count)}</strong> (${s.cust_share_pct}%)</td>
        <td><strong>${formatCurrency(s.total_revenue)}</strong> (${s.rev_share_pct}%)</td>
        <td>${formatCurrency(s.avg_monetary)}</td>
        <td>${s.avg_frequency} orders</td>
        <td>${s.avg_recency} days</td>
      </tr>
    `
    )
    .join("");
}

function renderCohortMatrix(cohortsData) {
  const tableEl = document.getElementById("cohortMatrixTable");
  if (!tableEl || !cohortsData || !cohortsData.cohorts) return;

  let headerHtml = `
    <thead>
      <tr>
        <th style="text-align: left;">Acquisition Cohort</th>
        <th>Customers</th>
        ${cohortsData.months.map((m) => `<th>${m}</th>`).join("")}
      </tr>
    </thead>
    <tbody>
  `;

  let rowsHtml = cohortsData.cohorts
    .map((c) => {
      let cells = c.rates
        .map((r, i) => {
          if (r === null) return `<td class="heat-none">-</td>`;
          let heatClass = "heat-vlow";
          if (i === 0) heatClass = "heat-100";
          else if (r >= 40) heatClass = "heat-high";
          else if (r >= 25) heatClass = "heat-mid-high";
          else if (r >= 15) heatClass = "heat-mid";
          else if (r >= 8) heatClass = "heat-low";

          return `<td><span class="cohort-cell ${heatClass}" style="display:inline-block; padding:4px 6px; width:100%;">${r.toFixed(1)}%</span></td>`;
        })
        .join("");

      return `
        <tr>
          <td style="text-align: left; font-weight: 600;">${c.cohort}</td>
          <td>${formatNumber(c.size)}</td>
          ${cells}
        </tr>
      `;
    })
    .join("");

  tableEl.innerHTML = headerHtml + rowsHtml + `</tbody>`;
}

// -------------------------------------------------------------
// 3. Products Catalog Page
// -------------------------------------------------------------
async function loadProductsCatalog() {
  const category = document.getElementById("categoryFilter") ? document.getElementById("categoryFilter").value : "All";
  const sortBy = document.getElementById("productSort") ? document.getElementById("productSort").value : "revenue";

  try {
    const res = await fetch(`/api/products?category=${encodeURIComponent(category)}&sort_by=${sortBy}&direction=desc`);
    const data = await res.json();
    renderProductsTable(data.products);
  } catch (err) {
    console.error("Failed to load products:", err);
  }
}

function renderProductsTable(products) {
  const tbody = document.getElementById("productsTableBody");
  if (!tbody) return;

  if (!products || products.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding: 24px; color: var(--text-muted);">No products found.</td></tr>`;
    return;
  }

  tbody.innerHTML = products
    .map(
      (p) => `
      <tr>
        <td><strong>#${p.id}</strong></td>
        <td>
          <div style="font-weight: 600;">${p.name}</div>
        </td>
        <td><span class="badge badge-neutral">${p.category}</span></td>
        <td>${formatCurrency(p.retail_price)}</td>
        <td>${formatNumber(p.units_sold)}</td>
        <td><strong>${formatCurrency(p.revenue)}</strong></td>
        <td style="color: #059669; font-weight: 600;">${formatCurrency(p.profit)}</td>
        <td>
          <span class="badge ${p.margin_pct >= 50 ? "badge-success" : p.margin_pct >= 35 ? "badge-primary" : "badge-warning"}">
            ${formatPercent(p.margin_pct)}
          </span>
        </td>
      </tr>
    `
    )
    .join("");
}

// -------------------------------------------------------------
// 4. Orders Ledger & Detail Modals
// -------------------------------------------------------------
let currentOrdersPage = 1;

async function loadOrdersLedger(page = 1) {
  currentOrdersPage = page;
  const search = document.getElementById("orderSearch") ? document.getElementById("orderSearch").value : "";
  const status = document.getElementById("orderStatusFilter") ? document.getElementById("orderStatusFilter").value : "All";

  const params = new URLSearchParams({
    page: page,
    per_page: 15,
    search: search,
    status: status
  });

  try {
    const res = await fetch(`/api/orders?${params.toString()}`);
    const data = await res.json();
    renderOrdersTable(data);
  } catch (err) {
    console.error("Failed to load orders:", err);
  }
}

function renderOrdersTable(data) {
  const tbody = document.getElementById("ordersTableBody");
  const paginationInfo = document.getElementById("paginationInfo");
  const prevBtn = document.getElementById("btnPrevPage");
  const nextBtn = document.getElementById("btnNextPage");

  if (!tbody) return;

  if (!data.orders || data.orders.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding: 28px; color: var(--text-muted);">No orders found matching criteria.</td></tr>`;
    if (paginationInfo) paginationInfo.innerText = "0 orders found";
    return;
  }

  const statusBadges = {
    "Completed": "badge-success",
    "Processing": "badge-primary",
    "Cancelled": "badge-danger",
    "Refunded": "badge-warning"
  };

  tbody.innerHTML = data.orders
    .map(
      (o) => `
      <tr class="clickable-row" onclick="viewOrderDetail(${o.order_id})">
        <td><strong>#${o.order_id}</strong></td>
        <td>${o.order_date.split(" ")[0]}</td>
        <td>
          <div style="font-weight: 600; cursor: pointer; color: var(--color-primary);" onclick="event.stopPropagation(); viewCustomerProfile(${o.customer_id});">
            ${o.customer_name}
          </div>
          <div style="font-size: 0.74rem; color: var(--text-muted);">${o.customer_email}</div>
        </td>
        <td><span class="badge ${statusBadges[o.status] || "badge-neutral"}">${o.status}</span></td>
        <td>${o.payment_method}</td>
        <td>${o.items_count} items</td>
        <td><strong>${formatCurrency(o.total_amount)}</strong></td>
        <td style="color: #059669; font-weight: 600;">${formatCurrency(o.total_profit)}</td>
      </tr>
    `
    )
    .join("");

  if (paginationInfo) {
    const start = (data.current_page - 1) * data.per_page + 1;
    const end = Math.min(data.current_page * data.per_page, data.total_records);
    paginationInfo.innerText = `Showing ${start}-${end} of ${formatNumber(data.total_records)} orders`;
  }

  if (prevBtn) prevBtn.disabled = data.current_page <= 1;
  if (nextBtn) nextBtn.disabled = data.current_page >= data.total_pages;
}

// Modal open/close helpers
async function viewOrderDetail(orderId) {
  try {
    const res = await fetch(`/api/order/${orderId}`);
    if (!res.ok) return;
    const data = await res.json();
    const modal = document.getElementById("orderModal");
    const modalBody = document.getElementById("orderModalContent");

    const order = data.order;
    const itemsHtml = data.items
      .map(
        (it) => `
        <tr>
          <td>${it.product_name} <span class="badge badge-neutral">${it.category}</span></td>
          <td style="text-align: center;">${it.quantity}</td>
          <td style="text-align: right;">${formatCurrency(it.unit_price)}</td>
          <td style="text-align: right; font-weight: 600;">${formatCurrency(it.total_price)}</td>
        </tr>
      `
      )
      .join("");

    modalBody.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 12px; border-bottom: 1px solid var(--border-color);">
        <div>
          <h3 style="font-size: 1.15rem; font-weight: 700;">Order #${order.order_id}</h3>
          <div style="color: var(--text-muted); font-size: 0.82rem;">Placed on ${order.order_date}</div>
        </div>
        <div>
          <span class="badge badge-success">${order.status}</span>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 14px; background: #f8fafc; padding: 12px; border-radius: 8px; font-size: 0.85rem;">
        <div>
          <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase;">Customer</div>
          <strong>${order.customer_name}</strong>
          <div>${order.customer_email}</div>
          <div style="color: var(--text-muted);">${order.customer_city || ""}, ${order.customer_country || ""}</div>
        </div>
        <div>
          <div style="color: var(--text-muted); font-size: 0.75rem; text-transform: uppercase;">Payment Details</div>
          <div>Method: <strong>${order.payment_method}</strong></div>
          <div>Shipping Cost: ${formatCurrency(order.shipping_cost)}</div>
          <div>Total Profit: <span style="color:#059669; font-weight:600;">${formatCurrency(order.total_profit)}</span></div>
        </div>
      </div>

      <div>
        <h4 style="font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; color: var(--text-muted);">Line Items</h4>
        <table class="data-table" style="font-size: 0.82rem;">
          <thead>
            <tr>
              <th>Product</th>
              <th style="text-align: center;">Qty</th>
              <th style="text-align: right;">Unit Price</th>
              <th style="text-align: right;">Total</th>
            </tr>
          </thead>
          <tbody>
            ${itemsHtml}
          </tbody>
          <tfoot>
            <tr>
              <td colspan="3" style="text-align: right; font-weight: 700;">Order Total:</td>
              <td style="text-align: right; font-weight: 700; font-size: 1rem; color: var(--color-primary);">${formatCurrency(order.total_amount)}</td>
            </tr>
          </tfoot>
        </table>
      </div>
    `;

    modal.classList.add("active");
  } catch (err) {
    console.error("Failed to load order details:", err);
  }
}

async function viewCustomerProfile(customerId) {
  try {
    const res = await fetch(`/api/customer/${customerId}`);
    if (!res.ok) return;
    const data = await res.json();
    const modal = document.getElementById("orderModal");
    const modalBody = document.getElementById("orderModalContent");

    const c = data.customer;
    const m = data.metrics;

    const ordersHtml = data.orders
      .slice(0, 8)
      .map(
        (o) => `
        <tr>
          <td>#${o.order_id}</td>
          <td>${o.order_date.split(" ")[0]}</td>
          <td><span class="badge badge-success">${o.status}</span></td>
          <td>${formatCurrency(o.total_amount)}</td>
        </tr>
      `
      )
      .join("");

    modalBody.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; padding-bottom: 12px; border-bottom: 1px solid var(--border-color);">
        <div>
          <h3 style="font-size: 1.15rem; font-weight: 700;">${c.name}</h3>
          <div style="color: var(--text-muted); font-size: 0.82rem;">${c.email} • Joined ${c.signup_date.split(" ")[0]}</div>
          <div style="color: var(--text-muted); font-size: 0.82rem;">${c.city || ""}, ${c.country || ""}</div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; background: #f8fafc; padding: 12px; border-radius: 8px; text-align: center;">
        <div>
          <div style="color: var(--text-muted); font-size: 0.72rem; text-transform: uppercase;">Total Spent</div>
          <div style="font-weight: 700; font-size: 1.05rem; color: var(--color-primary);">${formatCurrency(m.total_spent)}</div>
        </div>
        <div>
          <div style="color: var(--text-muted); font-size: 0.72rem; text-transform: uppercase;">Orders</div>
          <div style="font-weight: 700; font-size: 1.05rem;">${m.order_count}</div>
        </div>
        <div>
          <div style="color: var(--text-muted); font-size: 0.72rem; text-transform: uppercase;">AOV</div>
          <div style="font-weight: 700; font-size: 1.05rem;">${formatCurrency(m.aov)}</div>
        </div>
        <div>
          <div style="color: var(--text-muted); font-size: 0.72rem; text-transform: uppercase;">Profit Generated</div>
          <div style="font-weight: 700; font-size: 1.05rem; color: #059669;">${formatCurrency(m.total_profit)}</div>
        </div>
      </div>

      <div>
        <h4 style="font-size: 0.85rem; font-weight: 600; text-transform: uppercase; margin-bottom: 8px; color: var(--text-muted);">Recent Orders</h4>
        <table class="data-table" style="font-size: 0.82rem;">
          <thead>
            <tr>
              <th>Order ID</th>
              <th>Date</th>
              <th>Status</th>
              <th>Amount</th>
            </tr>
          </thead>
          <tbody>
            ${ordersHtml}
          </tbody>
        </table>
      </div>
    `;

    modal.classList.add("active");
  } catch (err) {
    console.error("Failed to load customer profile:", err);
  }
}

function closeModal() {
  const modal = document.getElementById("orderModal");
  if (modal) modal.classList.remove("active");
}
