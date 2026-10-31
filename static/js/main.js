/**
 * Grayeye IT Asset Management System - Frontend Logic
 * Lightweight Vanilla JavaScript (no external framework dependencies)
 */

document.addEventListener("DOMContentLoaded", function () {
  // 1. Alert Dismissal Handler
  const closeButtons = document.querySelectorAll(".alert-close");
  closeButtons.forEach(function (btn) {
    btn.addEventListener("click", function () {
      const alertBox = btn.closest(".alert");
      if (alertBox) {
        alertBox.style.opacity = "0";
        setTimeout(() => alertBox.remove(), 150);
      }
    });
  });

  // 2. Delete Confirmation Modal Handler
  const deleteModal = document.getElementById("deleteConfirmModal");
  const modalAssetId = document.getElementById("modalAssetId");
  const modalAssetName = document.getElementById("modalAssetName");
  const modalDeleteForm = document.getElementById("modalDeleteForm");
  const modalCancelBtn = document.getElementById("modalCancelBtn");
  const modalCloseCross = document.getElementById("modalCloseCross");

  function openDeleteModal(assetId, assetName) {
    if (!deleteModal) return;
    if (modalAssetId) modalAssetId.textContent = assetId;
    if (modalAssetName) modalAssetName.textContent = assetName;
    if (modalDeleteForm) {
      modalDeleteForm.action = `/assets/${encodeURIComponent(assetId)}/delete`;
    }
    deleteModal.classList.add("active");
    deleteModal.setAttribute("aria-hidden", "false");
  }

  function closeDeleteModal() {
    if (!deleteModal) return;
    deleteModal.classList.remove("active");
    deleteModal.setAttribute("aria-hidden", "true");
  }

  // Attach click listener to all delete buttons that specify data-asset-id
  document.querySelectorAll("[data-delete-trigger]").forEach(function (trigger) {
    trigger.addEventListener("click", function (e) {
      e.preventDefault();
      const assetId = trigger.getAttribute("data-asset-id");
      const assetName = trigger.getAttribute("data-asset-name") || assetId;
      openDeleteModal(assetId, assetName);
    });
  });

  if (modalCancelBtn) {
    modalCancelBtn.addEventListener("click", closeDeleteModal);
  }
  if (modalCloseCross) {
    modalCloseCross.addEventListener("click", closeDeleteModal);
  }
  if (deleteModal) {
    deleteModal.addEventListener("click", function (e) {
      if (e.target === deleteModal) {
        closeDeleteModal();
      }
    });
  }

  // Close modal on Escape key
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && deleteModal && deleteModal.classList.contains("active")) {
      closeDeleteModal();
    }
  });

  // 3. Status vs Assigned Employee form helper
  const statusSelect = document.getElementById("status");
  const assignedToInput = document.getElementById("assigned_to");
  const departmentSelect = document.getElementById("department");

  if (statusSelect && assignedToInput) {
    function handleStatusChange() {
      const currentStatus = statusSelect.value;
      if (currentStatus === "Available") {
        assignedToInput.placeholder = "None (Hardware is available in stock)";
      } else if (currentStatus === "Assigned") {
        assignedToInput.placeholder = "e.g. Jane Doe (Required for assigned status)";
      } else if (currentStatus === "Under Maintenance") {
        assignedToInput.placeholder = "Optional: Tech / Custodian during repair";
      } else if (currentStatus === "Retired") {
        assignedToInput.placeholder = "Decommissioned (Leave blank or previous owner)";
      }
    }

    statusSelect.addEventListener("change", handleStatusChange);
    handleStatusChange();
  }
});
