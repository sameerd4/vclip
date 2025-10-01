const statusEl = document.getElementById("status");
const slideshowEl = document.getElementById("slideshow");
const imgEl = document.getElementById("slide");
const captionEl = document.getElementById("caption");
const prevBtn = document.getElementById("prev");
const nextBtn = document.getElementById("next");

let manifest = null;
let activeList = [];
let index = 0;
const mq = window.matchMedia("(orientation: portrait)");

prevBtn.addEventListener("click", () => advance(-1));
nextBtn.addEventListener("click", () => advance(1));
mq.addEventListener("change", () => {
  selectOrientation();
  render();
});

async function init() {
  try {
    const res = await fetch("/src/data/gallery.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    manifest = await res.json();
    statusEl.textContent = "Ready";
    selectOrientation();
    render();
  } catch (err) {
    statusEl.textContent = `Failed to load manifest: ${err.message}`;
  }
}

function selectOrientation() {
  if (!manifest) return;
  const key = mq.matches ? "vertical" : "landscape";
  activeList = manifest[key] || [];
  index = 0;
  const modeLabel = key === "vertical" ? "portrait" : "landscape";
  statusEl.textContent = `${activeList.length} photos — ${modeLabel} mode`;
}

function advance(delta) {
  if (activeList.length === 0) return;
  index = (index + delta + activeList.length) % activeList.length;
  render();
}

function render() {
  if (!manifest) return;
  if (activeList.length === 0) {
    slideshowEl.classList.add("hidden");
    captionEl.textContent = "";
    return;
  }
  slideshowEl.classList.remove("hidden");
  const entry = activeList[index];
  imgEl.src = `/${entry.path}`;
  captionEl.textContent = `${entry.source} · ${entry.lut}`;
}

init();
