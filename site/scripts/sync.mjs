// Copies the catalog and written lessons from the content folder into the site.
// Content lives one level up (catalog.json, courses/<course>/**/<lesson>.md) so the
// planning files and the site share one source of truth.
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(process.env.CONTENT_ROOT || "..");
const here = path.resolve(".");
fs.copyFileSync(path.join(root, "catalog.json"), path.join(here, "src/data/catalog.json"));

const outDir = path.join(here, "src/content/lessons");
fs.rmSync(outDir, { recursive: true, force: true });
let n = 0;
for (const course of fs.readdirSync(path.join(root, "courses"))) {
  const walk = (dir) => {
    for (const f of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, f.name);
      if (f.isDirectory()) walk(p);
      else if (f.name.endsWith(".md") && f.name !== "course.md") {
        // Links to other courses' course.md become site URLs (lesson pages sit one level below the course).
        const body = fs.readFileSync(p, "utf8").replace(/\]\(\.\.\/\.\.\/([^)]*?)course\.md/g, "](../../$1");
        const dest = path.join(outDir, course, f.name);
        fs.mkdirSync(path.dirname(dest), { recursive: true });
        fs.writeFileSync(dest, body);
        n++;
      }
    }
  };
  walk(path.join(root, "courses", course));
}
console.log(`synced catalog and ${n} written lesson(s)`);
