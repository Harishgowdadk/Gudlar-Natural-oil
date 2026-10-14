document.addEventListener("DOMContentLoaded", function () {
  // Mobile nav toggle
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".main-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () { nav.classList.toggle("nav-open"); });
  }

  // Phone inputs accept digits only, max 10
  document.querySelectorAll("input[data-phone]").forEach(function (input) {
    input.setAttribute("maxlength", "10");
    input.setAttribute("inputmode", "numeric");
    input.addEventListener("input", function () {
      this.value = this.value.replace(/\D/g, "").slice(0, 10);
    });
  });

  // Quantity steppers
  document.querySelectorAll(".qty-box").forEach(function (box) {
    var input = box.querySelector("input");
    var min = parseInt(input.getAttribute("min") || "1", 10);
    var max = parseInt(input.getAttribute("max") || "9999", 10);
    box.querySelectorAll("button").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var cur = parseInt(input.value || "1", 10);
        input.value = btn.dataset.step === "up" ? Math.min(max, cur + 1) : Math.max(min, cur - 1);
        if (box.dataset.autosubmit === "true") { box.closest("form").requestSubmit(); }
      });
    });
  });
});
