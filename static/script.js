// =======================
// STATE MANAGEMENT
// =======================

// Get server state passed from template
function getServerState() {
  const stateElement = document.getElementById("server-state");
  if (stateElement) {
    try {
      return JSON.parse(stateElement.textContent);
    } catch (e) {
      console.error("Error parsing server state:", e);
    }
  }
  return null;
}

// Restore form state from server data
function restoreFormState() {
  const state = getServerState();
  if (!state) return;

  // Restore selected chat
  if (state.selected_chat) {
    const chatSelect = document.getElementById("selected_chat");
    if (chatSelect) {
      chatSelect.value = state.selected_chat;
    }
  }

  // Show registered people as read-only if registration is complete
  if (state.registration_complete && state.registered_people) {
    const container = document.getElementById("people-container");
    if (container) {
      state.registered_people.forEach((personName, index) => {
        if (personName !== "Bryan Ugas") {
          // Skip default person
          addPersonReadOnly(personName, index);
        }
      });
    }
  }
}

// Add a read-only person entry (for showing previously registered people)
function addPersonReadOnly(name, index) {
  const container = document.getElementById("people-container");
  if (!container) return;

  const personDiv = document.createElement("div");
  personDiv.className =
    "person-entry p-4 border border-gray-200 rounded-lg bg-gray-100";
  personDiv.innerHTML = `
        <div class="flex items-center justify-between mb-3">
            <h3 class="text-lg font-medium text-gray-800">Persona ${index + 1} (Registrada)</h3>
            <div class="flex items-center space-x-2">
                <svg class="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <button type="button" onclick="removePerson(this)" class="text-red-600 hover:text-red-800 transition-colors">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        </div>
        <div class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Nombre:</label>
                <input type="text" name="people[${personCount}][name]" required 
                       class="w-full border border-gray-300 rounded-md p-2 bg-gray-100 text-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors"
                       value="${name}" readonly>
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Imagen:</label>
                <div class="flex items-center space-x-2">
                    <span class="text-sm text-gray-600">✓ Imagen ya registrada</span>
                    <input type="file" name="people[${personCount}][image]" accept="image/*" 
                           class="w-full border border-gray-300 rounded-md p-2 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 transition-colors"
                           title="Cambiar imagen (opcional)">
                </div>
            </div>
        </div>
    `;

  container.appendChild(personDiv);
  personCount++;
}

// =======================
// TIME MANAGEMENT
// =======================

function updateTime() {
  const now = new Date();
  const timeString = now.toLocaleTimeString("es-ES", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const timeElement = document.getElementById("current-time");
  if (timeElement) {
    timeElement.textContent = timeString;
  }
}

// =======================
// VIDEO PAGE FUNCTIONS
// =======================

function toggleFullscreen() {
  const videoContainer = document.querySelector(".bg-white .bg-black");

  if (!videoContainer) {
    // Fallback to document fullscreen if video container not found
    if (!document.fullscreenElement) {
      document.documentElement.requestFullscreen().catch((err) => {
        console.log("Error attempting to enable fullscreen:", err);
      });
    } else {
      document.exitFullscreen().catch((err) => {
        console.log("Error attempting to exit fullscreen:", err);
      });
    }
    return;
  }

  if (!document.fullscreenElement) {
    videoContainer.requestFullscreen().catch((err) => {
      console.log("Error attempting to enable video fullscreen:", err);
      // Fallback to document fullscreen
      document.documentElement.requestFullscreen().catch((err2) => {
        console.log("Error attempting to enable document fullscreen:", err2);
      });
    });
  } else {
    document.exitFullscreen().catch((err) => {
      console.log("Error attempting to exit fullscreen:", err);
    });
  }
}

function refreshVideo() {
  const videoImg = document.getElementById("video-stream");
  if (videoImg) {
    const currentSrc = videoImg.src;
    videoImg.src = "";
    setTimeout(() => {
      videoImg.src = currentSrc + "?t=" + new Date().getTime();
    }, 100);
  }
}

function downloadSnapshot() {
  const videoImg = document.getElementById("video-stream");
  if (videoImg) {
    // Create a canvas to capture the current frame
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");

    canvas.width = videoImg.naturalWidth || videoImg.width;
    canvas.height = videoImg.naturalHeight || videoImg.height;

    ctx.drawImage(videoImg, 0, 0);

    // Create download link
    const link = document.createElement("a");
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    link.download = `snapshot-${timestamp}.jpg`;
    link.href = canvas.toDataURL("image/jpeg", 0.9);

    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }
}

function initVideoHandlers() {
  const videoImg = document.getElementById("video-stream");
  const loadingOverlay = document.getElementById("loading-overlay");

  if (!videoImg || !loadingOverlay) return;

  videoImg.onload = function () {
    loadingOverlay.classList.add("hidden");
  };

  videoImg.onerror = function () {
    loadingOverlay.classList.remove("hidden");
    loadingOverlay.innerHTML = `
            <div class="text-white text-center">
                <svg class="w-12 h-12 mx-auto mb-2 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <p class="text-sm">Error al cargar el video</p>
                <button onclick="refreshVideo()" class="mt-2 px-3 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700">
                    Reintentar
                </button>
            </div>
        `;
  };
}

// =======================
// REGISTRATION FORM FUNCTIONS
// =======================

function resetForm() {
  if (confirm("¿Estás seguro de que quieres limpiar el formulario?")) {
    const form = document.getElementById("registration-form");
    const peopleContainer = document.getElementById("people-container");
    const response = document.getElementById("response");

    if (form) form.reset();
    if (peopleContainer) peopleContainer.innerHTML = "";
    if (response) response.classList.add("hidden");

    // Reset person counter
    personCount = 0;
  }
}

// Person management for registration form
let personCount = 0;

function addPerson() {
  const container = document.getElementById("people-container");
  if (!container) return;

  const personDiv = document.createElement("div");
  personDiv.className =
    "person-entry p-4 border border-gray-200 rounded-lg bg-white";
  personDiv.innerHTML = `
        <div class="flex items-center justify-between mb-3">
            <h3 class="text-lg font-medium text-gray-800">Persona ${personCount + 1}</h3>
            <button type="button" onclick="removePerson(this)" class="text-red-600 hover:text-red-800 transition-colors">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
        <div class="space-y-4">
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Nombre:</label>
                <input type="text" name="people[${personCount}][name]" required 
                       class="w-full border border-gray-300 rounded-md p-2 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors"
                       placeholder="Ingresa el nombre de la persona">
            </div>
            <div>
                <label class="block text-sm font-medium text-gray-700 mb-1">Imagen:</label>
                <input type="file" name="people[${personCount}][image]" accept="image/*" required 
                       class="w-full border border-gray-300 rounded-md p-2 bg-white text-gray-900 focus:outline-none focus:ring-2 focus:ring-indigo-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 transition-colors">
            </div>
        </div>
    `;

  container.appendChild(personDiv);
  personCount++;
}

function removePerson(button) {
  const personDiv = button.closest(".person-entry");
  if (personDiv) {
    personDiv.remove();
    updatePersonNumbers();
  }
}

function updatePersonNumbers() {
  const personEntries = document.querySelectorAll(".person-entry");
  personEntries.forEach((entry, index) => {
    const title = entry.querySelector("h3");
    if (title) {
      const isRegistered = title.textContent.includes("(Registrada)");
      title.textContent = `Persona ${index + 1}${isRegistered ? " (Registrada)" : ""}`;
    }

    // Update input names
    const nameInput = entry.querySelector('input[type="text"]');
    const fileInput = entry.querySelector('input[type="file"]');

    if (nameInput) nameInput.name = `people[${index}][name]`;
    if (fileInput) fileInput.name = `people[${index}][image]`;
  });

  personCount = personEntries.length;
}

// Form submission handler
function handleFormSubmission() {
  const form = document.getElementById("registration-form");
  if (!form) return;

  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const submitBtn = document.getElementById("submit-btn");
    const response = document.getElementById("response");
    const selectedChat = document.getElementById("selected_chat");

    // Validate chat selection
    if (!selectedChat || !selectedChat.value) {
      alert("Por favor selecciona un chat antes de enviar el registro.");
      return;
    }

    // Validate that at least one person is added
    const peopleEntries = document.querySelectorAll(".person-entry");
    if (peopleEntries.length === 0) {
      alert(
        "Por favor añade al menos una persona antes de enviar el registro.",
      );
      return;
    }

    // Validate that all person entries are complete
    let isValid = true;
    peopleEntries.forEach((entry, index) => {
      const nameInput = entry.querySelector('input[type="text"]');
      const fileInput = entry.querySelector('input[type="file"]');

      if (!nameInput.value.trim()) {
        alert(`Por favor ingresa el nombre para la Persona ${index + 1}.`);
        isValid = false;
        return;
      }

      // Skip file validation for read-only entries (already registered)
      const isReadOnly = nameInput.readOnly;
      if (!isReadOnly && (!fileInput.files || fileInput.files.length === 0)) {
        alert(`Por favor selecciona una imagen para la Persona ${index + 1}.`);
        isValid = false;
        return;
      }
    });

    if (!isValid) return;

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `
                <div class="flex items-center justify-center space-x-2">
                    <div class="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Procesando...</span>
                </div>
            `;
    }

    try {
      const formData = new FormData();

      // Add chat selection
      formData.append("caretaker_chat_id", selectedChat.value);

      // Add people data
      peopleEntries.forEach((entry, index) => {
        const nameInput = entry.querySelector('input[type="text"]');
        const fileInput = entry.querySelector('input[type="file"]');

        formData.append(`people[${index}][name]`, nameInput.value.trim());

        // Only add file if it's not a read-only entry and has a file
        if (!nameInput.readOnly && fileInput.files && fileInput.files[0]) {
          formData.append(`people[${index}][image]`, fileInput.files[0]);
        }
      });

      const result = await fetch("/register", {
        method: "POST",
        body: formData,
      });

      if (!result.ok) {
        throw new Error(`HTTP error! status: ${result.status}`);
      }

      const data = await result.json();

      if (response) {
        response.textContent = JSON.stringify(data, null, 2);
        response.classList.remove("hidden");
      }

      // Show success message and reload page to update state
      alert("¡Registro completado exitosamente!");
      window.location.reload();
    } catch (error) {
      console.error("Registration error:", error);
      if (response) {
        response.textContent = `Error: ${error.message}`;
        response.classList.remove("hidden");
      }
      alert(`Error al procesar el registro: ${error.message}`);
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = `
                    <div class="flex items-center justify-center space-x-2">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <span>Enviar registro</span>
                    </div>
                `;
      }
    }
  });
}

// =======================
// KEYBOARD SHORTCUTS
// =======================

document.addEventListener("keydown", function (e) {
  // Alt + R for reset form (only on registration page)
  if (
    e.altKey &&
    e.key === "r" &&
    document.getElementById("registration-form")
  ) {
    e.preventDefault();
    resetForm();
  }

  // F for fullscreen (only on video page)
  if (
    (e.key === "f" || e.key === "F") &&
    document.getElementById("video-stream")
  ) {
    e.preventDefault();
    toggleFullscreen();
  }

  // Escape to exit fullscreen
  if (e.key === "Escape" && document.fullscreenElement) {
    document.exitFullscreen();
  }

  // Space to refresh video (only on video page)
  if (e.key === " " && document.getElementById("video-stream")) {
    e.preventDefault();
    refreshVideo();
  }
});

// =======================
// INITIALIZATION
// =======================

document.addEventListener("DOMContentLoaded", function () {
  // Start time updates
  updateTime();
  setInterval(updateTime, 1000);

  // Initialize registration form if present
  if (document.getElementById("registration-form")) {
    // Restore form state from server
    restoreFormState();

    handleFormSubmission();

    // Add person button handler
    const addPersonBtn = document.getElementById("add-person");
    if (addPersonBtn) {
      addPersonBtn.addEventListener("click", addPerson);
    }
  }

  // Initialize video handlers if present
  if (document.getElementById("video-stream")) {
    initVideoHandlers();
  }
});
