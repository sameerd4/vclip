const statusEl = document.getElementById("status");
const slideshowEl = document.getElementById("slideshow");
const slideContainer = document.querySelector(".slides");
const captionEl = document.getElementById("caption");
const prevBtn = document.getElementById("prev");
const nextBtn = document.getElementById("next");
const backdropEl = document.getElementById("backdrop");

let manifest = null;
let activeList = [];
let index = 0;
let autoplayTimer = null;
const AUTOPLAY_MS = 6500;
const mq = window.matchMedia("(orientation: portrait)");

prevBtn.addEventListener("click", () => {
  advance(-1);
  restartAutoplay();
});
nextBtn.addEventListener("click", () => {
  advance(1);
  restartAutoplay();
});
mq.addEventListener("change", () => {
  selectOrientation();
  render(true);
});

document.addEventListener("visibilitychange", () => {
  if (document.hidden) {
    stopAutoplay();
  } else {
    restartAutoplay();
  }
});

async function init() {
  try {
    const res = await fetch("data/gallery.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    manifest = await res.json();
    statusEl.textContent = "";
    selectOrientation();
    render(true);
    startAutoplay();
  } catch (err) {
    statusEl.textContent = `Failed to load manifest: ${err.message}`;
  }
}

function selectOrientation() {
  if (!manifest) return;
  const key = mq.matches ? "vertical" : "landscape";
  activeList = manifest[key] || [];
  index = Math.min(index, Math.max(activeList.length - 1, 0));
  const modeLabel = key === "vertical" ? "portrait" : "landscape";
  statusEl.textContent = `${activeList.length} photos — ${modeLabel} mode`;
}

function advance(delta) {
  if (activeList.length === 0) return;
  index = (index + delta + activeList.length) % activeList.length;
  render();
}

function render(force = false) {
  if (!manifest) return;
  if (activeList.length === 0) {
    slideshowEl.classList.add("hidden");
    captionEl.textContent = "";
    slideContainer.innerHTML = "";
    return;
  }
  slideshowEl.classList.remove("hidden");

  const current = activeList[index];
  const existing = slideContainer.querySelector(`[data-path="${current.path}"]`);

  if (force) {
    slideContainer.innerHTML = "";
  }

  let incoming = existing;
  if (!incoming) {
    incoming = createSlide(current);
    slideContainer.appendChild(incoming);
    requestAnimationFrame(() => incoming.classList.add("visible"));
  } else {
    incoming.classList.add("visible");
  }

  for (const slide of [...slideContainer.children]) {
    if (slide === incoming) continue;
    slide.classList.remove("visible");
    slide.addEventListener(
      "transitionend",
      () => {
        if (!slide.classList.contains("visible")) {
          slide.remove();
        }
      },
      { once: true }
    );
  }

  captionEl.textContent = `${current.source} · ${current.lut}`;
  updateBackdrop(incoming.querySelector("img"));
}

function createSlide(entry) {
  const wrapper = document.createElement("div");
  wrapper.className = "slide";
  wrapper.dataset.path = entry.path;

  const img = document.createElement("img");
  img.src = entry.path;
  img.alt = `${entry.source} — ${entry.lut}`;

  wrapper.appendChild(img);
  return wrapper;
}

function updateBackdrop(img) {
  if (!img || !backdropEl) return;
  const average = dominantShadowColor(img);
  backdropEl.style.background = `radial-gradient(circle at top, ${average}, transparent 60%), var(--backdrop-dark)`;
}

function dominantShadowColor(img) {
  try {
    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d", { willReadFrequently: true });
    const width = (canvas.width = 50);
    const height = (canvas.height = 50);
    context.drawImage(img, 0, 0, width, height);
    const data = context.getImageData(0, 0, width, height).data;
    let r = 0, g = 0, b = 0;
    for (let i = 0; i < data.length; i += 4) {
      r += data[i];
      g += data[i + 1];
      b += data[i + 2];
    }
    const count = data.length / 4;
    r = Math.round(r / count);
    g = Math.round(g / count);
    b = Math.round(b / count);
    return `rgba(${r}, ${g}, ${b}, 0.35)`;
  } catch {
    return "rgba(15, 23, 42, 0.35)";
  }
}

function startAutoplay() {
  stopAutoplay();
  if (activeList.length <= 1) return;
  autoplayTimer = window.setInterval(() => advance(1), AUTOPLAY_MS);
}

function stopAutoplay() {
  if (autoplayTimer !== null) {
    window.clearInterval(autoplayTimer);
    autoplayTimer = null;
  }
}

function restartAutoplay() {
  stopAutoplay();
  startAutoplay();
}

init();
