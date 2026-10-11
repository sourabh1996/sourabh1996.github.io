import catalog from "../data/catalog.json";

export const slugify = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
export const url = (p = "") => `${import.meta.env.BASE_URL.replace(/\/$/, "")}/${p}`.replace(/\/+$/, "") + "/";

export const courses = catalog.map((c) => ({
  ...c,
  modules: c.modules.map((m, i) => ({
    ...m,
    index: i + 1,
    lessons: m.lessons.map((l) => ({ ...l, slug: slugify(l.title) })),
  })),
}));

export const tracks = [...new Set(courses.map((c) => c.track))];
export const courseBySlug = (slug) => courses.find((c) => c.slug === slug);

// Flat reading order for previous / next links.
export function lessonsInOrder(course) {
  return course.modules.flatMap((m) => m.lessons.map((l) => ({ ...l, module: m })));
}

export const ICON = { "Track 1": "🐍", "Track 2": "📊", "Track 3": "🤖", "Track 4": "⚙️", "Track 5": "🧠", "Track 6": "✨", "Track 7": "🕹️", "Track 8": "🚀" };
export const iconFor = (c) => ICON[c.track.split(" ·")[0]] || "📘";
