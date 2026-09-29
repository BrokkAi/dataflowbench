// Layout helpers shared by the scatter charts: a value axis fitted to the data
// it has to show, and point labels placed so that they do not collide.
//
// Everything here works in SVG user units and is deterministic, so a chart
// renders identically on every build and its geometry can be tested without
// a browser.

export interface PercentAxis {
  min: number;
  max: number;
  ticks: number[];
}

/** A 0–100 axis trimmed at the bottom to the lowest value it must show.
 *
 * The floor never rises above `ceiling` (so a reference line such as the
 * 50% blind baseline stays inside the plot) and drops to the next multiple of
 * `step` below the lowest value, so nothing sits on the bottom edge. */
export function percentAxis(values: number[], ceiling = 50, step = 10): PercentAxis {
  const min =
    values.length === 0
      ? ceiling
      : Math.max(0, Math.min(ceiling, Math.floor((Math.min(...values) - step / 4) / step) * step));
  const ticks: number[] = [];
  for (let tick = min; tick <= 100; tick += step) ticks.push(tick);
  return { min, max: 100, ticks };
}

export interface LabelInput {
  x: number;
  y: number;
  text: string;
}

export interface LabelPlacement {
  x: number;
  y: number;
  anchor: 'start' | 'middle' | 'end';
  /** True when the label had to move far enough from its point to need a leader line. */
  leader: boolean;
}

export interface LabelOptions {
  /** The rectangle labels must stay inside. */
  bounds: { left: number; top: number; right: number; bottom: number };
  /** Point radius, including its stroke. */
  radius?: number;
  /** Label font size in user units. */
  fontSize?: number;
  /** Average advance per character as a fraction of the font size. */
  charWidth?: number;
}

interface Box {
  left: number;
  top: number;
  right: number;
  bottom: number;
}

const overlapArea = (a: Box, b: Box) =>
  Math.max(0, Math.min(a.right, b.right) - Math.max(a.left, b.left)) *
  Math.max(0, Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top));

/** Place one label per point, greedily, avoiding other labels, other points
 * and the plot edge.
 *
 * Points are placed in order of how crowded their neighbourhood is, most
 * crowded first, so the points with the fewest free positions choose before
 * the open ones take them. Each label tries the eight compass positions at
 * increasing distance; the first ring is preferred, and a label that has to go
 * further out is flagged for a leader line back to its point. */
export function placeLabels(points: LabelInput[], options: LabelOptions): LabelPlacement[] {
  const radius = options.radius ?? 8;
  const fontSize = options.fontSize ?? 12;
  const charWidth = options.charWidth ?? 0.6;
  const { bounds } = options;
  const ascent = fontSize * 0.72;
  const descent = fontSize * 0.22;
  const pad = 2;

  const pointBoxes: Box[] = points.map((point) => ({
    left: point.x - radius,
    top: point.y - radius,
    right: point.x + radius,
    bottom: point.y + radius,
  }));

  const crowding = points.map((point) =>
    points.reduce((count, other) => count + (Math.hypot(other.x - point.x, other.y - point.y) < 90 ? 1 : 0), 0),
  );
  const order = points.map((_, index) => index).sort((a, b) => crowding[b] - crowding[a] || a - b);

  const directions: { dx: number; dy: number; anchor: LabelPlacement['anchor'] }[] = [
    { dx: 1, dy: 0, anchor: 'start' },
    { dx: -1, dy: 0, anchor: 'end' },
    { dx: 0, dy: -1, anchor: 'middle' },
    { dx: 0, dy: 1, anchor: 'middle' },
    { dx: 1, dy: -1, anchor: 'start' },
    { dx: -1, dy: -1, anchor: 'end' },
    { dx: 1, dy: 1, anchor: 'start' },
    { dx: -1, dy: 1, anchor: 'end' },
  ];
  const rings = [radius + 4, radius + 18, radius + 34, radius + 54];

  const placed: Box[] = [];
  const result: LabelPlacement[] = new Array(points.length);

  for (const index of order) {
    const point = points[index];
    const width = point.text.length * fontSize * charWidth;
    let best: { score: number; placement: LabelPlacement; box: Box } | undefined;

    rings.forEach((distance, ring) => {
      directions.forEach((direction, preference) => {
        // Diagonals sit on the circle, not on the square around it.
        const scale = direction.dx !== 0 && direction.dy !== 0 ? Math.SQRT1_2 : 1;
        const anchorX = point.x + direction.dx * distance * scale;
        // Vertical offsets are measured to the text's near edge, not its baseline.
        const edgeY = point.y + direction.dy * distance * scale;
        const baseline =
          direction.dy < 0 ? edgeY - descent : direction.dy > 0 ? edgeY + ascent : point.y + (ascent - descent) / 2;
        const left =
          direction.anchor === 'start' ? anchorX : direction.anchor === 'end' ? anchorX - width : anchorX - width / 2;
        const box: Box = {
          left: left - pad,
          top: baseline - ascent - pad,
          right: left + width + pad,
          bottom: baseline + descent + pad,
        };

        let score = ring * 1000 + preference;
        for (const other of placed) score += overlapArea(box, other) * 100;
        pointBoxes.forEach((other, otherIndex) => {
          if (otherIndex !== index) score += overlapArea(box, other) * 60;
        });
        const outside =
          Math.max(0, bounds.left - box.left) +
          Math.max(0, box.right - bounds.right) +
          Math.max(0, bounds.top - box.top) +
          Math.max(0, box.bottom - bounds.bottom);
        score += outside * 5000;

        if (!best || score < best.score) {
          best = { score, box, placement: { x: anchorX, y: baseline, anchor: direction.anchor, leader: ring > 1 } };
        }
      });
    });

    placed.push(best!.box);
    result[index] = best!.placement;
  }

  return result;
}
