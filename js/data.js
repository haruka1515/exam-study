// Loading and shaping of the on-disk data: the manifest and the question sets.

const DATA = "data/";

/** Fetch JSON, with an error message that says which file failed. */
async function getJson(path) {
  let res;
  try {
    res = await fetch(path, { cache: "no-cache" });
  } catch (e) {
    // Almost always file:// — fetch is blocked for local files.
    throw new Error(
      `Could not read ${path}. If the address bar starts with "file://", ` +
        `the browser blocks local file reads — run tools/serve.ps1 and use http://localhost:8080.`
    );
  }
  if (!res.ok) throw new Error(`${path} → HTTP ${res.status}`);
  try {
    return await res.json();
  } catch (e) {
    throw new Error(`${path} is not valid JSON — ${e.message}`);
  }
}

export function loadManifest() {
  return getJson(DATA + "manifest.json");
}

export function loadProfiles() {
  return getJson("prompts/profiles.json").catch(() => ({}));
}

export function loadSet(file) {
  return getJson(DATA + file);
}

/**
 * Flatten the manifest into one row per section, which is what every view
 * actually wants to iterate over.
 */
export function flattenSections(manifest) {
  const out = [];
  for (const ch of manifest.chapters ?? []) {
    for (const sec of ch.sections ?? []) {
      out.push({
        setId: `${ch.id}-${sec.id}`,
        chapterId: ch.id,
        chapterNumber: ch.number,
        chapterTitle: ch.title,
        profile: ch.profile,
        sectionId: sec.id,
        sectionNumber: sec.number,
        sectionTitle: sec.title,
        file: sec.file,
        status: sec.status ?? "pending",
      });
    }
  }
  return out;
}

/** Whole-manifest placeholder check, so the UI can nudge you to fill it in. */
export function countPlaceholders(manifest) {
  let n = 0;
  const isTodo = (s) => typeof s === "string" && s.trim().toUpperCase().startsWith("TODO");
  if (isTodo(manifest.course)) n++;
  if (isTodo(manifest.exam)) n++;
  for (const ch of manifest.chapters ?? []) {
    if (isTodo(ch.title)) n++;
    for (const sec of ch.sections ?? []) if (isTodo(sec.title)) n++;
  }
  return n;
}

/** Days until the exam, or null if the date is missing or still a placeholder. */
export function daysUntil(dateStr) {
  if (!dateStr || !/^\d{4}-\d{2}-\d{2}$/.test(dateStr.trim())) return null;
  const then = new Date(dateStr.trim() + "T00:00:00");
  if (Number.isNaN(then.getTime())) return null;
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  return Math.round((then - today) / 86400000);
}
