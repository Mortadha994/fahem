/**
 * The number a student reads for a chapter.
 *
 * A chapter id is one global key, so each year owns a block of ids (the same
 * arithmetic as app/core/chapter_ids.py - keep the two in step):
 *
 *   2ème -> 1..29   (id = number)
 *   3ème -> 31..59  (id = 30 + number)
 *   Bac  -> 61..89  (id = 60 + number)
 *
 * "Chapitre 31" is how the platform names the first 3ème chapter; the student
 * should read "Chapitre 1". Anything outside the blocks is returned as it came.
 */
const BLOCKS = [
  { niveau: "bac", offset: 60 },
  { niveau: "3eme", offset: 30 },
  { niveau: "2eme", offset: 0 },
];
const BLOCK = 30;

function blockOf(id) {
  const n = Number.parseInt(id, 10);
  if (!Number.isInteger(n) || String(n) !== String(id).trim()) return null;
  return BLOCKS.find((b) => n > b.offset && n < b.offset + BLOCK) ?? null;
}

export function chapterNumber(id) {
  const block = blockOf(id);
  return block ? String(Number.parseInt(id, 10) - block.offset) : String(id);
}

/** The year a chapter id belongs to ("2eme" / "3eme" / "bac"), or null. A chat
 *  is scoped by (niveau, chapitre), so the niveau has to follow the chapter. */
export function niveauOfChapter(id) {
  return blockOf(id)?.niveau ?? null;
}
