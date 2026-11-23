/**
 * Pehchan Unisex Salon & Beauty Parlour - Core Frontend JavaScript
 */

const API_BASE = window.location.origin;

// Mobile Navigation Toggle
document.addEventListener("DOMContentLoaded", () => {
  const toggleBtn = document.getElementById("mobileToggle");
  const navMenu = document.getElementById("navMenu");

  if (toggleBtn && navMenu) {
    toggleBtn.addEventListener("click", () => {
      const isOpen = navMenu.classList.toggle("open");
      document.body.style.overflow = isOpen ? "hidden" : "";
      const icon = toggleBtn.querySelector("i");
      if (icon) {
        if (isOpen) {
          icon.classList.remove("fa-bars");
          icon.classList.add("fa-times");
        } else {
          icon.classList.remove("fa-times");
          icon.classList.add("fa-bars");
        }
      }
    });

    // Close on link click
    navMenu.querySelectorAll(".nav-link, .nav-cta").forEach(link => {
      link.addEventListener("click", () => {
        navMenu.classList.remove("open");
        document.body.style.overflow = "";
        const icon = toggleBtn.querySelector("i");
        if (icon) {
          icon.classList.remove("fa-times");
          icon.classList.add("fa-bars");
        }
      });
    });

    // Close on escape key
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && navMenu.classList.contains("open")) {
        navMenu.classList.remove("open");
        document.body.style.overflow = "";
        const icon = toggleBtn.querySelector("i");
        if (icon) {
          icon.classList.remove("fa-times");
          icon.classList.add("fa-bars");
        }
      }
    });
  }

  // FAQ Accordion
  initFaqAccordion();
});

// Toast Notification Engine
function showToast(message, type = "info") {
  let container = document.querySelector(".toast-container");
  if (!container) {
    container = document.createElement("div");
    container.className = "toast-container";
    document.body.appendChild(container);
  }

  const toast = document.createElement("div");
  toast.className = `toast toast-${type}`;
  toast.innerHTML = `
    <div style="display:flex; align-items:center; gap:10px;">
      <i class="fas ${type === 'success' ? 'fa-check-circle text-gold' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
      <span>${message}</span>
    </div>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// FAQ Accordion Handler
function initFaqAccordion() {
  const faqItems = document.querySelectorAll(".faq-item");
  faqItems.forEach(item => {
    const header = item.querySelector(".faq-header");
    if (header) {
      header.addEventListener("click", () => {
        const isActive = item.classList.contains("active");
        faqItems.forEach(i => i.classList.remove("active"));
        if (!isActive) {
          item.classList.add("active");
        }
      });
    }
  });
}

// Format Currency
function formatCurrency(amount) {
  return "₹" + Number(amount).toLocaleString("en-IN");
}

// Global API Helpers
const PehchanAPI = {
  async getCategories() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/services/categories`);
      return await res.json();
    } catch (e) {
      console.error("Failed to load categories:", e);
      return [];
    }
  },

  async getServices(categorySlug = null, gender = null, featuredOnly = false) {
    try {
      let url = `${API_BASE}/api/v1/services?`;
      if (categorySlug) url += `category_slug=${encodeURIComponent(categorySlug)}&`;
      if (gender) url += `gender=${encodeURIComponent(gender)}&`;
      if (featuredOnly) url += `featured_only=true&`;
      const res = await fetch(url);
      return await res.json();
    } catch (e) {
      console.error("Failed to load services:", e);
      return [];
    }
  },

  async getStaff() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/staff`);
      return await res.json();
    } catch (e) {
      console.error("Failed to load staff:", e);
      return [];
    }
  },

  async getSlots(serviceId, date, staffId = null) {
    try {
      let url = `${API_BASE}/api/v1/bookings/slots?service_id=${serviceId}&date=${date}`;
      if (staffId) url += `&staff_id=${staffId}`;
      const res = await fetch(url);
      return await res.json();
    } catch (e) {
      console.error("Failed to calculate slots:", e);
      return { slots: [] };
    }
  },

  async createBooking(payload) {
    const res = await fetch(`${API_BASE}/api/v1/bookings`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || "Unable to complete booking");
    }
    return data;
  },

  async getOffers() {
    try {
      const res = await fetch(`${API_BASE}/api/v1/public/offers`);
      return await res.json();
    } catch (e) {
      console.error("Failed to load offers:", e);
      return [];
    }
  },

  async getGallery(category = null, bridalOnly = false) {
    try {
      let url = `${API_BASE}/api/v1/public/gallery?`;
      if (category) url += `category=${category}&`;
      if (bridalOnly) url += `bridal_only=true&`;
      const res = await fetch(url);
      return await res.json();
    } catch (e) {
      console.error("Failed to load gallery:", e);
      return [];
    }
  },

  async getReviews(featuredOnly = false) {
    try {
      let url = `${API_BASE}/api/v1/public/reviews`;
      if (featuredOnly) url += `?featured_only=true`;
      const res = await fetch(url);
      return await res.json();
    } catch (e) {
      console.error("Failed to load reviews:", e);
      return [];
    }
  },

  async submitReview(payload) {
    const res = await fetch(`${API_BASE}/api/v1/public/reviews`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    return await res.json();
  },

  async trackBooking(reference) {
    const res = await fetch(`${API_BASE}/api/v1/bookings/track/${reference}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Booking not found");
    return data;
  }
};
