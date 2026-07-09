document.addEventListener("submit", (event) => {
  const form = event.target;
  if (!form.classList.contains("scll-upload")) return;
  const button = form.querySelector("button[type='submit']");
  if (button) button.disabled = true;
});
