"use strict";

document.addEventListener("DOMContentLoaded", () => {
    const startButton = document.getElementById("startCamera");
    const captureButton = document.getElementById("capturePhoto");
    const stopButton = document.getElementById("stopCamera");

    const video = document.getElementById("camera");
    const fileInput = document.getElementById("imageFile");
    const preview = document.getElementById("preview");
    const message = document.getElementById("cameraMessage");

    const photoForm = document.getElementById("photoForm");
    const clearForm = document.getElementById("clearForm");
    const peekButton = document.getElementById("peekButton");
    const peekMessage = document.getElementById("peekMessage");

    let stream = null;
    let previewUrl = null;

    function showMessage(text) {
        if (message) {
            message.textContent = text;
        }
    }

    function stopCamera() {
        if (stream) {
            stream.getTracks().forEach((track) => track.stop());
            stream = null;
        }

        if (video) {
            video.srcObject = null;
        }

        if (startButton) {
            startButton.disabled = !fileInput || fileInput.disabled;
        }

        if (captureButton) {
            captureButton.disabled = true;
        }

        if (stopButton) {
            stopButton.disabled = true;
        }
    }

    function showPreview(file) {
        if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
        }

        previewUrl = URL.createObjectURL(file);
        preview.src = previewUrl;
        preview.classList.remove("d-none");
    }

    if (startButton) {
        startButton.addEventListener("click", async () => {
            try {
                if (!navigator.mediaDevices?.getUserMedia) {
                    throw new Error("La cámara no está disponible.");
                }

                startButton.disabled = true;

                stream = await navigator.mediaDevices.getUserMedia({
                    video: {
                        facingMode: { ideal: "environment" }
                    },
                    audio: false
                });

                video.srcObject = stream;
                await video.play();

                captureButton.disabled = false;
                stopButton.disabled = false;

                showMessage(
                    "Cámara activada. Pulsa «Tomar foto y apilar»."
                );
            } catch (error) {
                stopCamera();

                showMessage(
                    "No se pudo abrir la cámara. Revisa los permisos " +
                    "o selecciona una fotografía."
                );

                console.error("Error de cámara:", error);
            }
        });
    }

    if (captureButton) {
        captureButton.addEventListener("click", () => {
            if (!stream || !video.videoWidth) {
                showMessage("Abre la cámara antes de tomar la foto.");
                return;
            }

            const canvas = document.createElement("canvas");
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;

            const context = canvas.getContext("2d");

            if (!context) {
                showMessage("No se pudo preparar la fotografía.");
                return;
            }

            context.drawImage(video, 0, 0);

            canvas.toBlob((blob) => {
                if (!blob) {
                    showMessage("No se pudo capturar la fotografía.");
                    return;
                }

                const file = new File(
                    [blob],
                    "captura.jpg",
                    { type: "image/jpeg" }
                );

                const transfer = new DataTransfer();
                transfer.items.add(file);
                fileInput.files = transfer.files;

                showPreview(file);
                stopCamera();

                showMessage(
                    "Foto capturada. Se agregará a la pila al confirmar."
                );

                photoForm.requestSubmit();
            }, "image/jpeg", 0.9);
        });
    }

    if (stopButton) {
        stopButton.addEventListener("click", () => {
            stopCamera();
            showMessage("Cámara cerrada.");
        });
    }

    if (fileInput) {
        fileInput.addEventListener("change", () => {
            const file = fileInput.files[0];

            if (!file) {
                return;
            }

            const allowedTypes = [
                "image/jpeg",
                "image/png",
                "image/webp"
            ];

            if (!allowedTypes.includes(file.type)) {
                fileInput.value = "";
                showMessage("Selecciona una imagen JPEG, PNG o WEBP.");
                return;
            }

            showPreview(file);
            showMessage("Imagen seleccionada. Puedes guardarla.");
        });
    }

    if (photoForm) {
        photoForm.addEventListener("submit", (event) => {
            if (!fileInput || !fileInput.files.length) {
                event.preventDefault();
                showMessage("Primero captura o selecciona una foto.");
                return;
            }

            stopCamera();
        });
    }

    if (peekButton && peekMessage) {
        peekButton.addEventListener("click", () => {
            peekMessage.classList.remove("d-none");

            if (!peekMessage.textContent.trim()) {
                peekMessage.textContent =
                    "El elemento superior se muestra en la sección «Tope».";
            }

            peekMessage.scrollIntoView({
                behavior: "smooth",
                block: "center"
            });
        });
    }

    if (clearForm) {
        clearForm.addEventListener("submit", (event) => {
            const confirmed = window.confirm(
                "¿Deseas eliminar todos los elementos de la pila?"
            );

            if (!confirmed) {
                event.preventDefault();
            }
        });
    }

    window.addEventListener("pagehide", () => {
        stopCamera();

        if (previewUrl) {
            URL.revokeObjectURL(previewUrl);
            previewUrl = null;
        }
    });
});