/**
 * Pehchan Unisex Salon - Admin Dashboard Controller
 * Full single-page management application with JWT authentication
 */

const API_BASE = window.location.origin;
let authToken = localStorage.getItem("pehchan_admin_token") || null;
let currentAdmin = null;

document.addEventListener("DOMContentLoaded", () => {
  initAuth();
  initSidebar();
  initEventListeners();
});

// Authentication Init
async function initAuth() {
  if (authToken) {
    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/me`, {
        headers: { "Authorization": `Bearer ${authToken}` }
      });
      if (res.ok) {
        const data = await res.json();
        currentAdmin = data.admin;
        showDashboard();
        return;
      }
    } catch (e) {
      console.error("Auth check failed:", e);
    }
  }
  showLogin();
}

function showLogin() {
  document.getElementById("loginOverlay").style.display = "flex";
  document.getElementById("adminAppWrapper").style.display = "none";
}

function showDashboard() {
  document.getElementById("loginOverlay").style.display = "none";
  document.getElementById("adminAppWrapper").style.display = "flex";
  if (currentAdmin) {
    document.getElementById("loggedAdminName").textContent = currentAdmin.full_name;
    document.getElementById("loggedAdminRole").textContent = currentAdmin.role.toUpperCase();
  }
  loadCurrentTabData("overview");
}

function initSidebar() {
  const sidebar = document.getElementById("adminSidebar");
  const toggleBtn = document.getElementById("adminSidebarToggle");
  const closeBtn = document.getElementById("sidebarCloseBtn");
  const backdrop = document.getElementById("sidebarBackdrop");

  const openSidebar = () => {
    if (sidebar) sidebar.classList.add("open");
    if (backdrop) backdrop.classList.add("active");
  };

  const closeSidebar = () => {
    if (sidebar) sidebar.classList.remove("open");
    if (backdrop) backdrop.classList.remove("active");
  };

  if (toggleBtn) toggleBtn.addEventListener("click", openSidebar);
  if (closeBtn) closeBtn.addEventListener("click", closeSidebar);
  if (backdrop) backdrop.addEventListener("click", closeSidebar);

  document.querySelectorAll(".menu-link").forEach(link => {
    link.addEventListener("click", () => {
      document.querySelectorAll(".menu-link").forEach(l => l.classList.remove("active"));
      link.classList.add("active");
      const tab = link.dataset.tab;
      switchTab(tab);
      closeSidebar();
    });
  });

  document.getElementById("logoutBtn").addEventListener("click", () => {
    localStorage.removeItem("pehchan_admin_token");
    authToken = null;
    currentAdmin = null;
    showLogin();
  });
}

function switchTab(tabName) {
  document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
  const target = document.getElementById(`panel-${tabName}`);
  if (target) target.classList.add("active");

  const titles = {
    overview: ["Overview & Statistics", "Real-time salon operations, active bookings and revenue health."],
    appointments: ["Appointments Management", "Manage, reschedule, confirm and complete client reservations."],
    customers: ["Customer CRM", "Client directory, visit counts and direct WhatsApp engagement."],
    services: ["Services & Pricing Menu", "Manage salon treatments, duration, pricing and featured tags."],
    staff: ["Stylists & Specialists Roster", "Manage stylist profiles, designations, ratings and working schedules."],
    offers: ["Offers & Festive Packages", "Create seasonal deals, discounts and package combinations."],
    gallery: ["Portfolio & Photographs", "Curate client transformation looks and bridal portfolio imagery."],
    reviews: ["Reviews & Testimonials", "Moderate customer feedback and feature glowing reviews on homepage."],
    settings: ["Salon Profile & Settings", "Configure opening hours, reception contacts and automation switches."],
    logs: ["Notification Audit Trail", "Real-time delivery records for WhatsApp Business Cloud API & Email."]
  };

  if (titles[tabName]) {
    document.getElementById("currentTabTitle").textContent = titles[tabName][0];
    document.getElementById("currentTabDesc").textContent = titles[tabName][1];
  }

  loadCurrentTabData(tabName);
}

function loadCurrentTabData(tabName) {
  if (tabName === "overview") loadSummary();
  else if (tabName === "appointments") loadAppointments();
  else if (tabName === "customers") loadCustomers();
  else if (tabName === "services") loadServices();
  else if (tabName === "staff") loadStaff();
  else if (tabName === "offers") loadOffers();
  else if (tabName === "gallery") loadGallery();
  else if (tabName === "reviews") loadReviews();
  else if (tabName === "settings") loadSettings();
  else if (tabName === "logs") loadLogs();
}

function initEventListeners() {
  // Login Form
  document.getElementById("adminLoginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const btn = document.getElementById("loginBtn");
    btn.disabled = true;
    btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Authenticating...`;

    try {
      const email = document.getElementById("loginEmail").value.trim();
      const password = document.getElementById("loginPassword").value;

      const res = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Authentication failed");

      authToken = data.access_token;
      localStorage.setItem("pehchan_admin_token", authToken);
      currentAdmin = data.admin;
      showDashboard();
    } catch (err) {
      alert("Login Error: " + err.message);
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i class="fas fa-lock-open"></i> Authenticate &amp; Enter`;
    }
  });

  // Refresh Data Button
  document.getElementById("refreshDataBtn").addEventListener("click", () => {
    const activeLink = document.querySelector(".menu-link.active");
    if (activeLink) loadCurrentTabData(activeLink.dataset.tab);
  });

  // Appointments filter & search
  document.getElementById("appStatusFilter").addEventListener("change", () => loadAppointments());
  document.getElementById("appSearchInput").addEventListener("input", () => loadAppointments());

  // Customer search
  document.getElementById("custSearchInput").addEventListener("input", (e) => loadCustomers(e.target.value));

  // Modal Open Buttons
  document.getElementById("openAddServiceModalBtn").addEventListener("click", () => openAddServiceModal());
  document.getElementById("openAddStaffModalBtn").addEventListener("click", () => openAddStaffModal());
  document.getElementById("openAddOfferModalBtn").addEventListener("click", () => {
    document.getElementById("offerModalForm").reset();
    document.getElementById("offerValidFrom").value = new Date().toISOString().split("T")[0];
    openModal("offerModalOverlay");
  });
  document.getElementById("openAddGalleryModalBtn").addEventListener("click", () => {
    document.getElementById("galleryModalForm").reset();
    openModal("galleryModalOverlay");
  });

  // Forms Submissions
  document.getElementById("serviceModalForm").addEventListener("submit", handleSaveService);
  document.getElementById("staffModalForm").addEventListener("submit", handleSaveStaff);
  document.getElementById("offerModalForm").addEventListener("submit", handleSaveOffer);
  document.getElementById("galleryModalForm").addEventListener("submit", handleSaveGallery);
  document.getElementById("rescheduleModalForm").addEventListener("submit", handleRescheduleSubmit);
  document.getElementById("salonSettingsForm").addEventListener("submit", handleSaveSettings);
}

// 1. Overview API
async function loadSummary() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/admin/summary`, {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (!res.ok) return;
    const s = await res.json();

    document.getElementById("kpiTodayAppointments").textContent = s.today_appointments;
    document.getElementById("kpiPendingAppointments").textContent = s.pending_appointments;
    document.getElementById("kpiTodayRevenue").textContent = "₹" + s.today_revenue.toLocaleString("en-IN");
    document.getElementById("kpiTotalCustomers").textContent = s.total_customers;

    const tbody = document.getElementById("overviewRecentTableBody");
    tbody.innerHTML = s.recent_bookings.map(r => `
      <tr>
        <td><strong style="color:var(--gold-primary);">#${r.booking_reference}</strong></td>
        <td>${r.customer_name}<br><small style="color:#888;">${r.customer_phone}</small></td>
        <td>${r.service_name}</td>
        <td>${r.appointment_date} @ ${r.start_time}</td>
        <td>${r.staff_name || 'Senior Stylist'}</td>
        <td>₹${r.total_price}</td>
        <td><span class="status-badge status-${r.status}">${r.status}</span></td>
        <td>
          <button class="btn-action" onclick="quickUpdateStatus('${r.id}', 'confirmed')" title="Confirm"><i class="fas fa-check text-gold"></i></button>
          <button class="btn-action" onclick="quickUpdateStatus('${r.id}', 'completed')" title="Complete"><i class="fas fa-check-double" style="color:#3498db;"></i></button>
          <button class="btn-action" onclick="quickUpdateStatus('${r.id}', 'cancelled')" title="Cancel"><i class="fas fa-times" style="color:#e74c3c;"></i></button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error("Failed to load summary:", e);
  }
}

// 2. Appointments API
async function loadAppointments() {
  const status = document.getElementById("appStatusFilter").value;
  const search = document.getElementById("appSearchInput").value.trim();
  let url = `${API_BASE}/api/v1/admin/appointments?`;
  if (status) url += `status_filter=${status}&`;
  if (search) url += `search=${encodeURIComponent(search)}&`;

  try {
    const res = await fetch(url, { headers: { "Authorization": `Bearer ${authToken}` } });
    if (!res.ok) return;
    const apps = await res.json();
    const tbody = document.getElementById("allAppointmentsTableBody");

    if (!apps.length) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:30px; color:#777;">No appointments found.</td></tr>`;
      return;
    }

    tbody.innerHTML = apps.map(a => `
      <tr>
        <td><strong style="color:var(--gold-light);">#${a.booking_reference}</strong></td>
        <td>
          <strong>${a.customer_name}</strong><br>
          <a href="https://wa.me/${a.customer_phone.replace(/[^0-9]/g, '')}" target="_blank" style="color:#25d366; font-size:0.8rem;">
            <i class="fab fa-whatsapp"></i> ${a.customer_phone}
          </a>
        </td>
        <td>${a.service_name} (${a.duration_minutes}m)</td>
        <td>${a.appointment_date} <br><span style="color:var(--gold-primary); font-weight:600;">${a.start_time} - ${a.end_time}</span></td>
        <td>${a.staff_name || 'Senior Specialist'}</td>
        <td style="font-weight:700; color:#fff;">₹${a.total_price}</td>
        <td><span class="status-badge status-${a.status}">${a.status}</span></td>
        <td>
          <div style="display:flex; gap:6px;">
            <select class="admin-select" style="padding:4px 8px; font-size:0.8rem;" onchange="updateAppointmentStatus('${a.id}', this.value)">
              <option value="">Change Status...</option>
              <option value="pending" ${a.status==='pending'?'disabled':''}>Pending</option>
              <option value="confirmed" ${a.status==='confirmed'?'disabled':''}>Confirmed</option>
              <option value="completed" ${a.status==='completed'?'disabled':''}>Completed</option>
              <option value="cancelled" ${a.status==='cancelled'?'disabled':''}>Cancelled</option>
            </select>
            <button class="btn-action" onclick="openRescheduleModal('${a.id}', '${a.appointment_date}', '${a.start_time}', '${a.staff_id || ''}', '${a.booking_reference}')" title="Reschedule Date/Time">
              <i class="far fa-clock"></i>
            </button>
            <button class="btn-action" onclick="deleteAppointment('${a.id}')" title="Delete Booking" style="color:#e74c3c;">
              <i class="far fa-trash-alt"></i>
            </button>
          </div>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error("Failed to load appointments:", e);
  }
}

async function quickUpdateStatus(appId, status) {
  await updateAppointmentStatus(appId, status);
  loadSummary();
}

async function updateAppointmentStatus(appId, status) {
  if (!status) return;
  try {
    const res = await fetch(`${API_BASE}/api/v1/admin/appointments/${appId}/status`, {
      method: "PATCH",
      headers: {
        "Authorization": `Bearer ${authToken}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ status })
    });
    if (res.ok) {
      loadAppointments();
    } else {
      const err = await res.json();
      alert("Failed: " + (err.detail || "Error"));
    }
  } catch (e) {
    console.error(e);
  }
}

async function deleteAppointment(appId) {
  if (!confirm("Are you sure you want to permanently delete this appointment?")) return;
  try {
    const res = await fetch(`${API_BASE}/api/v1/admin/appointments/${appId}`, {
      method: "DELETE",
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    if (res.ok) loadAppointments();
  } catch (e) {
    console.error(e);
  }
}

// 3. Customer CRM API
async function loadCustomers(search = "") {
  let url = `${API_BASE}/api/v1/admin/customers`;
  if (search) url += `?search=${encodeURIComponent(search)}`;
  try {
    const res = await fetch(url, { headers: { "Authorization": `Bearer ${authToken}` } });
    const custs = await res.json();
    const tbody = document.getElementById("customersTableBody");
    tbody.innerHTML = custs.map(c => `
      <tr>
        <td><strong>${c.full_name}</strong></td>
        <td>${c.phone}</td>
        <td>${c.email || '—'}</td>
        <td><span style="background:var(--gold-glow); color:var(--gold-light); padding:3px 10px; border-radius:50px; font-weight:700;">${c.total_visits} Visits</span></td>
        <td>${c.created_at ? c.created_at.split('T')[0] : '—'}</td>
        <td>
          <a href="https://wa.me/${c.phone.replace(/[^0-9]/g, '')}?text=Hello%20${encodeURIComponent(c.full_name)},%20greetings%20from%20Pehchan%20Unisex%20Salon!" target="_blank" class="btn-action" style="color:#25d366;">
            <i class="fab fa-whatsapp"></i> Chat on WhatsApp
          </a>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error(e);
  }
}

// 4. Services API
async function loadServices() {
  try {
    const [resServ, resCat] = await Promise.all([
      fetch(`${API_BASE}/api/v1/services`),
      fetch(`${API_BASE}/api/v1/services/categories`)
    ]);
    const services = await resServ.json();
    const categories = await resCat.json();

    // Populate category select in modal
    const catSelect = document.getElementById("servCategorySelect");
    catSelect.innerHTML = categories.map(c => `<option value="${c.id}">${c.name}</option>`).join("");

    const tbody = document.getElementById("adminServicesTableBody");
    tbody.innerHTML = services.map(s => `
      <tr>
        <td><strong>${s.name}</strong></td>
        <td>${s.category_name || 'General'}</td>
        <td>${s.duration_minutes} Mins</td>
        <td style="text-transform:capitalize;">${s.gender_target}</td>
        <td style="color:#fff; font-weight:600;">₹${s.price}</td>
        <td style="color:var(--gold-primary); font-weight:600;">${s.discount_price ? '₹'+s.discount_price : '—'}</td>
        <td>${s.is_featured ? '<i class="fas fa-check text-gold"></i>' : '—'}</td>
        <td>
          <button class="btn-action" onclick="openEditServiceModal('${s.id}')" title="Edit"><i class="fas fa-pencil-alt"></i></button>
          <button class="btn-action" onclick="deleteService('${s.id}')" title="Delete" style="color:#e74c3c;"><i class="fas fa-trash-alt"></i></button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error(e);
  }
}

function openAddServiceModal() {
  document.getElementById("serviceModalTitle").textContent = "Add Salon Service";
  document.getElementById("modalServiceId").value = "";
  document.getElementById("serviceModalForm").reset();
  openModal("serviceModalOverlay");
}

async function openEditServiceModal(id) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/services/${id}`);
    const s = await res.json();
    document.getElementById("serviceModalTitle").textContent = "Edit Salon Service";
    document.getElementById("modalServiceId").value = s.id;
    document.getElementById("servName").value = s.name;
    document.getElementById("servCategorySelect").value = s.category_id || "";
    document.getElementById("servDuration").value = s.duration_minutes;
    document.getElementById("servGender").value = s.gender_target;
    document.getElementById("servPrice").value = s.price;
    document.getElementById("servDiscountPrice").value = s.discount_price || "";
    document.getElementById("servImage").value = s.image_url || "";
    document.getElementById("servDesc").value = s.description || "";
    openModal("serviceModalOverlay");
  } catch (e) {
    console.error(e);
  }
}

async function handleSaveService(e) {
  e.preventDefault();
  const id = document.getElementById("modalServiceId").value;
  const payload = {
    name: document.getElementById("servName").value.trim(),
    category_id: document.getElementById("servCategorySelect").value || null,
    duration_minutes: parseInt(document.getElementById("servDuration").value, 10),
    gender_target: document.getElementById("servGender").value,
    price: parseInt(document.getElementById("servPrice").value, 10),
    discount_price: document.getElementById("servDiscountPrice").value ? parseInt(document.getElementById("servDiscountPrice").value, 10) : null,
    image_url: document.getElementById("servImage").value.trim() || null,
    description: document.getElementById("servDesc").value.trim() || null,
    is_featured: true,
    is_active: true
  };

  const url = id ? `${API_BASE}/api/v1/admin/services/${id}` : `${API_BASE}/api/v1/admin/services`;
  const method = id ? "PUT" : "POST";

  const res = await fetch(url, {
    method,
    headers: {
      "Authorization": `Bearer ${authToken}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (res.ok) {
    closeModal("serviceModalOverlay");
    loadServices();
  } else {
    alert("Error saving service");
  }
}

async function deleteService(id) {
  if (!confirm("Deactivate this service?")) return;
  await fetch(`${API_BASE}/api/v1/admin/services/${id}`, {
    method: "DELETE",
    headers: { "Authorization": `Bearer ${authToken}` }
  });
  loadServices();
}

// 5. Staff API
async function loadStaff() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/staff`);
    const staff = await res.json();
    const tbody = document.getElementById("adminStaffTableBody");
    tbody.innerHTML = staff.map(s => `
      <tr>
        <td><strong>${s.name}</strong></td>
        <td>${s.designation}</td>
        <td>${s.specialization || 'Master Artist'}</td>
        <td><i class="fas fa-star text-gold"></i> ${s.rating}</td>
        <td>${s.experience_years} Years</td>
        <td>${s.phone || '—'}</td>
        <td>
          <button class="btn-action" onclick="openEditStaffModal('${s.id}')" title="Edit"><i class="fas fa-pencil-alt"></i></button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error(e);
  }
}

function openAddStaffModal() {
  document.getElementById("staffModalTitle").textContent = "Add Specialist";
  document.getElementById("modalStaffId").value = "";
  document.getElementById("staffModalForm").reset();
  openModal("staffModalOverlay");
}

async function openEditStaffModal(id) {
  try {
    const res = await fetch(`${API_BASE}/api/v1/staff/${id}`);
    const s = await res.json();
    document.getElementById("staffModalTitle").textContent = "Edit Specialist";
    document.getElementById("modalStaffId").value = s.id;
    document.getElementById("staffName").value = s.name;
    document.getElementById("staffDesignation").value = s.designation;
    document.getElementById("staffSpecialization").value = s.specialization || "";
    document.getElementById("staffExp").value = s.experience_years;
    document.getElementById("staffRating").value = s.rating;
    document.getElementById("staffPhoto").value = s.photo_url || "";
    document.getElementById("staffBio").value = s.bio || "";
    openModal("staffModalOverlay");
  } catch (e) {
    console.error(e);
  }
}

async function handleSaveStaff(e) {
  e.preventDefault();
  const id = document.getElementById("modalStaffId").value;
  const payload = {
    name: document.getElementById("staffName").value.trim(),
    designation: document.getElementById("staffDesignation").value.trim(),
    specialization: document.getElementById("staffSpecialization").value.trim() || null,
    experience_years: parseInt(document.getElementById("staffExp").value, 10),
    rating: parseFloat(document.getElementById("staffRating").value),
    photo_url: document.getElementById("staffPhoto").value.trim() || null,
    bio: document.getElementById("staffBio").value.trim() || null,
    is_active: true
  };

  const url = id ? `${API_BASE}/api/v1/admin/staff/${id}` : `${API_BASE}/api/v1/admin/staff`;
  const method = id ? "PUT" : "POST";

  const res = await fetch(url, {
    method,
    headers: {
      "Authorization": `Bearer ${authToken}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (res.ok) {
    closeModal("staffModalOverlay");
    loadStaff();
  }
}

// 6. Offers API
async function loadOffers() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/public/offers`);
    const offers = await res.json();
    const tbody = document.getElementById("adminOffersTableBody");
    tbody.innerHTML = offers.map(o => `
      <tr>
        <td><strong>${o.title}</strong></td>
        <td><span class="status-badge status-confirmed">${o.badge_text || 'OFFER'}</span></td>
        <td>₹${o.original_price || '—'}</td>
        <td style="color:var(--gold-primary); font-weight:700;">₹${o.discounted_price}</td>
        <td>${o.discount_percentage ? o.discount_percentage + '%' : '—'}</td>
        <td>${o.valid_from} to ${o.valid_until}</td>
        <td>
          <button class="btn-action" onclick="deleteOffer('${o.id}')" title="Delete" style="color:#e74c3c;"><i class="fas fa-trash-alt"></i></button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error(e);
  }
}

async function handleSaveOffer(e) {
  e.preventDefault();
  const payload = {
    title: document.getElementById("offerTitle").value.trim(),
    badge_text: document.getElementById("offerBadge").value.trim() || null,
    original_price: document.getElementById("offerOrigPrice").value ? parseInt(document.getElementById("offerOrigPrice").value, 10) : null,
    discounted_price: parseInt(document.getElementById("offerDiscPrice").value, 10),
    valid_from: document.getElementById("offerValidFrom").value,
    valid_until: document.getElementById("offerValidUntil").value,
    included_services: document.getElementById("offerIncludes").value.trim() || null,
    image_url: document.getElementById("offerImg").value.trim() || null,
    description: document.getElementById("offerDesc").value.trim() || null,
    is_active: true
  };

  const res = await fetch(`${API_BASE}/api/v1/admin/offers`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${authToken}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (res.ok) {
    closeModal("offerModalOverlay");
    loadOffers();
  }
}

async function deleteOffer(id) {
  if (!confirm("Delete this promotional offer?")) return;
  await fetch(`${API_BASE}/api/v1/admin/offers/${id}`, {
    method: "DELETE",
    headers: { "Authorization": `Bearer ${authToken}` }
  });
  loadOffers();
}

// 7. Gallery API
async function loadGallery() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/public/gallery`);
    const items = await res.json();
    const tbody = document.getElementById("adminGalleryTableBody");
    tbody.innerHTML = items.map(g => `
      <tr>
        <td><img src="${g.image_url}" style="width:50px; height:50px; object-fit:cover; border-radius:4px;"></td>
        <td><strong>${g.title}</strong></td>
        <td style="text-transform:uppercase;">${g.category}</td>
        <td>${g.is_bridal_special ? '<i class="fas fa-crown text-gold"></i> Bridal' : '—'}</td>
        <td style="color:#aaa;">${g.caption || '—'}</td>
        <td>
          <button class="btn-action" onclick="deleteGallery('${g.id}')" title="Delete" style="color:#e74c3c;"><i class="fas fa-trash-alt"></i></button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error(e);
  }
}

async function handleSaveGallery(e) {
  e.preventDefault();
  const payload = {
    title: document.getElementById("galTitle").value.trim(),
    category: document.getElementById("galCategory").value,
    image_url: document.getElementById("galImgUrl").value.trim(),
    caption: document.getElementById("galCaption").value.trim() || null,
    is_bridal_special: document.getElementById("galIsBridal").checked,
    sort_order: 0
  };

  const res = await fetch(`${API_BASE}/api/v1/admin/gallery`, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${authToken}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (res.ok) {
    closeModal("galleryModalOverlay");
    loadGallery();
  }
}

async function deleteGallery(id) {
  if (!confirm("Remove photograph from portfolio?")) return;
  await fetch(`${API_BASE}/api/v1/admin/gallery/${id}`, {
    method: "DELETE",
    headers: { "Authorization": `Bearer ${authToken}` }
  });
  loadGallery();
}

// 8. Reviews Moderation API
async function loadReviews() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/admin/reviews`, {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    const reviews = await res.json();
    const tbody = document.getElementById("adminReviewsTableBody");
    tbody.innerHTML = reviews.map(r => `
      <tr>
        <td><strong>${r.reviewer_name}</strong></td>
        <td>${r.reviewer_location || '—'}</td>
        <td>${'⭐'.repeat(r.rating)}</td>
        <td style="max-width:300px;">"${r.comment}"</td>
        <td>
          <button class="btn-action" onclick="toggleReviewApproval('${r.id}')" style="color:${r.is_approved ? '#2ecc71' : '#e74c3c'};">
            ${r.is_approved ? 'Approved' : 'Hidden'}
          </button>
        </td>
        <td>
          <button class="btn-action" onclick="toggleReviewFeature('${r.id}')" style="color:${r.is_featured ? 'var(--gold-primary)' : '#888'};">
            ${r.is_featured ? '⭐ Featured' : 'Normal'}
          </button>
        </td>
        <td>
          <button class="btn-action" onclick="deleteReview('${r.id}')" title="Delete" style="color:#e74c3c;"><i class="fas fa-trash-alt"></i></button>
        </td>
      </tr>
    `).join("");
  } catch (e) {
    console.error(e);
  }
}

async function toggleReviewApproval(id) {
  await fetch(`${API_BASE}/api/v1/admin/reviews/${id}/toggle-approve`, {
    method: "PATCH",
    headers: { "Authorization": `Bearer ${authToken}` }
  });
  loadReviews();
}

async function toggleReviewFeature(id) {
  await fetch(`${API_BASE}/api/v1/admin/reviews/${id}/toggle-feature`, {
    method: "PATCH",
    headers: { "Authorization": `Bearer ${authToken}` }
  });
  loadReviews();
}

async function deleteReview(id) {
  if (!confirm("Delete review?")) return;
  await fetch(`${API_BASE}/api/v1/admin/reviews/${id}`, {
    method: "DELETE",
    headers: { "Authorization": `Bearer ${authToken}` }
  });
  loadReviews();
}

// 9. Settings API
async function loadSettings() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/admin/settings`, {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    const s = await res.json();
    document.getElementById("setSalonName").value = s.salon_name || "";
    document.getElementById("setTagline").value = s.tagline || "";
    document.getElementById("setPhone").value = s.phone || "";
    document.getElementById("setWhatsApp").value = s.whatsapp_number || "";
    document.getElementById("setEmail").value = s.email || "";
    document.getElementById("setAddress").value = s.address || "";
    document.getElementById("setSlotInterval").value = s.slot_interval_minutes || 30;
    document.getElementById("setOnlineBooking").checked = s.allow_online_booking;
    document.getElementById("setWhatsAppNotif").checked = s.whatsapp_notifications_enabled;
    document.getElementById("setEmailNotif").checked = s.email_notifications_enabled;
  } catch (e) {
    console.error(e);
  }
}

async function handleSaveSettings(e) {
  e.preventDefault();
  const payload = {
    salon_name: document.getElementById("setSalonName").value.trim(),
    tagline: document.getElementById("setTagline").value.trim(),
    phone: document.getElementById("setPhone").value.trim(),
    whatsapp_number: document.getElementById("setWhatsApp").value.trim(),
    email: document.getElementById("setEmail").value.trim(),
    address: document.getElementById("setAddress").value.trim(),
    slot_interval_minutes: parseInt(document.getElementById("setSlotInterval").value, 10),
    allow_online_booking: document.getElementById("setOnlineBooking").checked,
    whatsapp_notifications_enabled: document.getElementById("setWhatsAppNotif").checked,
    email_notifications_enabled: document.getElementById("setEmailNotif").checked
  };

  const res = await fetch(`${API_BASE}/api/v1/admin/settings`, {
    method: "PUT",
    headers: {
      "Authorization": `Bearer ${authToken}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (res.ok) alert("Salon settings saved successfully!");
}

// 10. Logs API
async function loadLogs() {
  try {
    const res = await fetch(`${API_BASE}/api/v1/admin/notification-logs`, {
      headers: { "Authorization": `Bearer ${authToken}` }
    });
    const logs = await res.json();
    const tbody = document.getElementById("adminLogsTableBody");

    if (!logs.length) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:30px; color:#777;">No notification logs recorded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = logs.map(l => `
      <tr>
        <td style="color:#aaa;">${l.sent_at}</td>
        <td>
          <span style="color:${l.channel==='whatsapp'?'#25d366':'#3498db'}; font-weight:700;">
            <i class="fab ${l.channel==='whatsapp'?'fa-whatsapp':'fa-envelope'}"></i> ${l.channel.toUpperCase()}
          </span>
        </td>
        <td>${l.recipient}</td>
        <td>${l.subject || '—'}</td>
        <td style="max-width:320px; font-size:0.82rem; color:#bbb;">${l.message_content.substring(0, 95)}...</td>
        <td><span class="status-badge status-${l.status==='sent'?'confirmed':'rescheduled'}">${l.status}</span></td>
      </tr>
    `).join("");
  } catch (e) {
    console.error(e);
  }
}

// Reschedule Modal
async function openRescheduleModal(appId, appDate, appTime, staffId, ref) {
  document.getElementById("reschedAppId").value = appId;
  document.getElementById("reschedDetailsNotice").textContent = `Rescheduling Reference #${ref}. Current slot: ${appDate} at ${appTime}`;
  document.getElementById("reschedDate").value = appDate;
  document.getElementById("reschedTime").value = appTime;

  // Load staff into select
  const staffRes = await fetch(`${API_BASE}/api/v1/staff`);
  const staffList = await staffRes.json();
  const sel = document.getElementById("reschedStaffSelect");
  sel.innerHTML = staffList.map(s => `<option value="${s.id}" ${s.id === staffId ? 'selected' : ''}>${s.name} (${s.designation})</option>`).join("");

  openModal("rescheduleModalOverlay");
}

async function handleRescheduleSubmit(e) {
  e.preventDefault();
  const appId = document.getElementById("reschedAppId").value;
  const payload = {
    appointment_date: document.getElementById("reschedDate").value,
    start_time: document.getElementById("reschedTime").value,
    staff_id: document.getElementById("reschedStaffSelect").value || null
  };

  const res = await fetch(`${API_BASE}/api/v1/admin/appointments/${appId}/reschedule`, {
    method: "PATCH",
    headers: {
      "Authorization": `Bearer ${authToken}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (res.ok) {
    closeModal("rescheduleModalOverlay");
    loadAppointments();
  } else {
    alert("Reschedule conflict or error");
  }
}

// Modal Helpers
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = "flex";
}

function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.style.display = "none";
}
