function addPerson() {
  const container = document.getElementById("people-container");
  const index = container.children.length;

  const personDiv = document.createElement("div");
  personDiv.className =
    "relative border border-gray-300 rounded-md p-6 bg-white shadow-sm";

  personDiv.dataset.index = index;

  personDiv.innerHTML = `
    <button type="button" aria-label="Eliminar persona" title="Eliminar persona" 
      class="absolute top-3 right-3 text-red-600 hover:text-red-800 font-bold text-xl focus:outline-none">&times;</button>

    <label for="person-name-${index}" class="block text-gray-700 font-medium mb-1">Nombre de la persona:</label>
    <input type="text" id="person-name-${index}" name="person_name" required
      class="w-full border border-gray-300 rounded-md p-2 mb-4 focus:outline-none focus:ring-2 focus:ring-indigo-500" />

    <label for="person-images-${index}" class="block text-gray-700 font-medium mb-1">Imágenes del rostro (múltiples):</label>
    <input type="file" id="person-images-${index}" name="person_images" accept="image/*" multiple required
      class="w-full" />
  `;

  container.appendChild(personDiv);

  personDiv.querySelector("button").addEventListener("click", () => {
    personDiv.remove();
  });
}

// Iniciar con un input de persona
addPerson();

document.getElementById("add-person").addEventListener("click", addPerson);

document
  .getElementById("registration-form")
  .addEventListener("submit", async (e) => {
    e.preventDefault();

    const responseDiv = document.getElementById("response");
    responseDiv.textContent = "";

    const caretakerName = document
      .getElementById("caretaker-name")
      .value.trim();
    const caretakerChatId = document
      .getElementById("caretaker-chat-id")
      .value.trim();

    if (!caretakerName || !caretakerChatId) {
      alert("Por favor completa la información del cuidador");
      return;
    }

    const peopleDivs = document.querySelectorAll("#people-container .person");
    if (peopleDivs.length === 0) {
      alert("Añade al menos una persona a cuidar");
      return;
    }

    const formData = new FormData();
    formData.append("caretaker_name", caretakerName);
    formData.append("caretaker_chat_id", caretakerChatId);

    let valid = true;

    peopleDivs.forEach((div, index) => {
      const personNameInput = div.querySelector('input[type="text"]');
      const imagesInput = div.querySelector('input[type="file"]');

      const personName = personNameInput.value.trim();

      if (!personName) {
        valid = false;
        alert("Por favor ingresa el nombre de todas las personas");
        return;
      }

      if (!imagesInput.files.length) {
        valid = false;
        alert(`Por favor sube al menos una imagen para ${personName}`);
        return;
      }

      formData.append(`people[${index}][name]`, personName);
      for (let i = 0; i < imagesInput.files.length; i++) {
        formData.append(`people[${index}][images]`, imagesInput.files[i]);
      }
    });

    if (!valid) return;

    responseDiv.textContent = "Procesando...";

    try {
      const res = await fetch("/register", {
        method: "POST",
        body: formData,
      });

      if (!res.ok) throw new Error(`Error del servidor: ${res.status}`);

      const json = await res.json();

      responseDiv.textContent = JSON.stringify(json, null, 2);
    } catch (err) {
      responseDiv.textContent = "Error: " + err.message;
    }
  });
