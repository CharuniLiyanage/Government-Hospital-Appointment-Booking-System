const menuBtn = document.getElementById("menuBtn");
const mobileMenu = document.getElementById("mobileMenu");
const overlay = document.getElementById("overlay");
const modal = document.getElementById("modal");
const confirmationCard = document.getElementById("confirmationCard");

menuBtn.onclick = () => {
    mobileMenu.classList.toggle("open");
    overlay.classList.toggle("active");
};

overlay.onclick = () => {
    mobileMenu.classList.remove("open");
    overlay.classList.remove("active");
    modal.style.display = "none";
};

document.getElementById("bookNowBtn").onclick = () => {
    modal.style.display = "flex";
    overlay.classList.add("active");
};

document.querySelector(".close").onclick = () => {
    modal.style.display = "none";
    overlay.classList.remove("active");
};

document.getElementById("bookAppointment").onclick = () => {
    modal.style.display = "flex";
    overlay.classList.add("active");
};

document.getElementById("myAppointments").onclick = () => {
    window.location.href = "/my_appointments";
};

document.getElementById("searchDoctor").onclick = () => {
    window.location.href = "/view_doctors";
};


// -------- FORM SUBMIT --------
document.getElementById("appointmentForm").addEventListener("submit", async function (e) {
    e.preventDefault();

    const formData = new FormData(this);

    try {
        const res = await fetch("/book", { method: "POST", body: formData });
        const data = await res.json();

        confirmationCard.style.display = "block";

        if (!res.ok || data.status === "error") {
            confirmationCard.className = "confirmation-card error";
            confirmationCard.innerHTML = "❌ " + data.message;
            return;
        }

        confirmationCard.className = "confirmation-card";
        confirmationCard.innerHTML = `
            ✅ Appointment Confirmed<br>
            Ref No: <strong>${data.reference_no}</strong>
        `;

        this.reset();
        modal.style.display = "none";
        overlay.classList.remove("active");

    } catch {
        confirmationCard.className = "confirmation-card error";
        confirmationCard.innerHTML = "❌ Server error. Try again.";
        confirmationCard.style.display = "block";
    }
});
