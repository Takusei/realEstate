/* eslint-disable @typescript-eslint/no-explicit-any */

export type StationInfo = {
  line: string | null;
  name: string | null;
  walk_minutes: number | null;
};

export type Flags = {
  pet_ok: boolean;
  south_facing: boolean;
  corner: boolean;
  balcony: boolean;
  tower_mansion: boolean;
};

export type NormalizedDoc = {
  _id_str: string | null;
  address: string;
  built_year: number | null;
  built_month: number | null;
  type: string;
  desc: string;
  image_url: string;
  building_name: string;
  price_yen: number | null;
  monthly_payment_yen: number | null;
  area_sqm: number | null;
  layout_raw: string | null;
  rooms: number | null;
  ldk: boolean | null;
  station: StationInfo;
  flags: Flags;
  url: string;
  created_at: string | null; // ISO string
  embedding: number[] | null;
};

// ---------- Helpers ----------

export const z2h = (s?: string | null): string =>
  (s ?? "").normalize("NFKC").trim();

const tryJsonParse = (raw: string): any | null => {
  try {
    return JSON.parse(raw);
  } catch {
    try {
      // Common case: embedded quotes doubled and whole thing quoted
      const s2 = raw.replace(/""/g, '"').replace(/^"+|"+$/g, "");
      return JSON.parse(s2);
    } catch {
      return null;
    }
  }
};

const parseOid = (s: string): string | null => {
  const obj = tryJsonParse(s);
  return obj?.$oid ?? null;
};

const parseBsonDate = (s: string): string | null => {
  const obj = tryJsonParse(s);
  const ds: string | null = obj?.$date ?? null;
  if (!ds) return null;
  // new Date(...) will handle Z properly; return ISO string
  const d = new Date(ds);
  return isNaN(d.getTime()) ? null : d.toISOString();
};

export const parseBuiltYM = (s: string): { built_year: number | null; built_month: number | null } => {
  const t = z2h(s);
  let m = t.match(/(\d{4})\s*年\s*(\d{1,2})\s*月/);
  if (m) return { built_year: Number(m[1]), built_month: Number(m[2]) };
  m = t.match(/(\d{4})\s*年/);
  if (m) return { built_year: Number(m[1]), built_month: null };
  return { built_year: null, built_month: null };
};

export const parsePriceToYen = (s?: string | null): number | null => {
  if (!s) return null;
  const t = z2h(s).replace(/,/g, "");
  // X億Y万
  let m = t.match(/(\d+(?:\.\d+)?)\s*億\s*(\d+(?:\.\d+)?)?\s*万?円?/);
  if (m) {
    const oku = parseFloat(m[1]);
    const man = m[2] ? parseFloat(m[2]) : 0;
    return Math.round(oku * 100_000_000 + man * 10_000);
  }
  // Z万円
  m = t.match(/(\d+(?:\.\d+)?)\s*万\s*円?/);
  if (m) return Math.round(parseFloat(m[1]) * 10_000);
  // pure yen
  m = t.match(/(\d+)\s*円/);
  if (m) return parseInt(m[1], 10);
  return null;
};

export const parseMonthlyPaymentToYen = (s?: string | null): number | null => {
  if (!s) return null;
  const t = z2h(s).replace(/,/g, "");
  const m = t.match(/月々支払額[:：]?\s*(\d+(?:\.\d+)?)\s*万\s*円?/);
  return m ? Math.round(parseFloat(m[1]) * 10_000) : null;
};

export const parseAreaSqm = (s?: string | null): number | null => {
  if (!s) return null;
  const t = z2h(s);
  const m = t.match(/(\d+(?:\.\d+)?)\s*(?:m2|㎡)/i);
  return m ? parseFloat(m[1]) : null;
};

export const parseLayout = (
  s?: string | null
): { layout_raw: string | null; rooms: number | null; ldk: boolean | null } => {
  const t = z2h(s);
  if (!t) return { layout_raw: null, rooms: null, ldk: null };

  // Prefer value after "間取り："
  const mBlock = t.match(/間取り[:：]?\s*([^\s／/|]+)/);
  const layoutRaw = mBlock ? mBlock[1] : t;

  if (layoutRaw.includes("ワンルーム")) {
    return { layout_raw: layoutRaw, rooms: 0, ldk: false };
  }
  // e.g., 1LDK, 2DK, 3K
  let m = layoutRaw.match(/(\d+)\s*(L?D?K)/i);
  if (m) {
    const rooms = parseInt(m[1], 10);
    const kind = m[2].toUpperCase();
    const isLDK = kind.includes("LDK") || (kind.includes("L") && kind.includes("K"));
    return { layout_raw: layoutRaw, rooms, ldk: isLDK };
  }
  // 1K only
  m = layoutRaw.match(/(\d+)\s*K/i);
  if (m) {
    return { layout_raw: layoutRaw, rooms: parseInt(m[1], 10), ldk: false };
  }
  return { layout_raw: layoutRaw, rooms: null, ldk: null };
};

export const parseStationBlock = (s?: string | null): StationInfo => {
  const t = z2h(s);
  if (!t) return { line: null, name: null, walk_minutes: null };

  // walk minutes
  const walkM = t.match(/徒歩\s*(\d+)\s*分/);
  const walk = walkM ? parseInt(walkM[1], 10) : null;

  let line: string | null = null;
  let name: string | null = null;

  if (t.includes("/")) {
    const parts = t.split("/");
    if (parts.length >= 2) {
      line = parts[0].trim();
      // station name before dash/徒歩
      const after = parts[1];
      const stationPart = after.split(/[-－–—]|徒歩/)[0]?.trim();
      name = stationPart || null;
    }
  } else {
    const mLine = t.match(/(.+?線)/);
    if (mLine) line = mLine[1].trim();
    const mName = t.match(/\/\s*([^\s－\-–—/]+)/);
    if (mName) name = mName[1].trim();
  }
  return { line, name, walk_minutes: walk };
};

export const detectFlags = (...texts: (string | null | undefined)[]): Flags => {
  const joined = z2h(texts.filter(Boolean).join(" "));
  return {
    pet_ok: /ペット可|ペット相談/.test(joined),
    south_facing: /南向き/.test(joined),
    corner: /角部屋/.test(joined),
    balcony: /バルコニー/.test(joined),
    tower_mansion: /タワー?マンション|シティタワー/.test(joined),
  };
};