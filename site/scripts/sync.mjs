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

// Lesson files link to each other the way they sit in the repo (…/course.md, …/<module>/<lesson>.md),
// so links also work on GitHub. On the site every lesson is /courses/<course>/<lesson>/ and every
// course is /courses/<course>/, and a lesson page sits one level below its course page.
function siteLink(fromCourseRel, target) {
  // Resolve the link against the course folder, then rebuild it from the lesson page's URL.
  const parts = path.posix.normalize(path.posix.join("courses", "COURSE", fromCourseRel.split(path.sep).join("/"), target)).split("/");
  const name = parts.pop();
  // parts now starts with "courses"; parts[1] is the target course (or COURSE for the same one).
  const targetCourse = parts[1];
  const coursePrefix = targetCourse === "COURSE" ? "../" : `../../${targetCourse}/`;
  return name === "course" ? coursePrefix : `${coursePrefix}${name}/`;
}
for (const course of fs.readdirSync(path.join(root, "courses"))) {
  const walk = (dir) => {
    for (const f of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, f.name);
      if (f.isDirectory()) walk(p);
      else if (f.name.endsWith(".md") && f.name !== "course.md") {
        const body = fs.readFileSync(p, "utf8").replace(/\]\(((?:\.\.\/)*)([^)#\s]*?)\.md(#[^)\s]*)?\)/g, (m, up, target, hash = "") =>
          target.includes(":") ? m : `](${siteLink(path.relative(path.join(root, "courses", course), path.join(dir, up)), target)}${hash})`);
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
