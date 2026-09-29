import assert from 'node:assert/strict';
import test from 'node:test';
import { percentAxis, placeLabels } from './scatter-layout.ts';

test('the percent axis keeps 50% in view and trims empty space below', () => {
  assert.deepEqual(percentAxis([78, 86, 100]), { min: 50, max: 100, ticks: [50, 60, 70, 80, 90, 100] });
  assert.equal(percentAxis([45, 90]).min, 40);
  // A point just above a tick would sit on the axis; it gets the tick below.
  assert.equal(percentAxis([41.2, 90]).min, 30);
  // A value on a tick still gets room beneath it.
  assert.equal(percentAxis([30]).min, 20);
  assert.equal(percentAxis([]).min, 50);
  assert.equal(percentAxis([-5]).min, 0);
});

const bounds = { left: 0, top: 0, right: 800, bottom: 400 };

function boxes(points: { x: number; y: number; text: string }[]) {
  return placeLabels(points, { bounds, fontSize: 12, charWidth: 0.6 }).map((label, index) => {
    const width = points[index].text.length * 7.2;
    const left = label.anchor === 'start' ? label.x : label.anchor === 'end' ? label.x - width : label.x - width / 2;
    return { left, right: left + width, top: label.y - 8.6, bottom: label.y + 2.6 };
  });
}

test('labels of a tight cluster do not overlap one another', () => {
  const cluster = [
    { x: 200, y: 120, text: 'OpenTaint' },
    { x: 206, y: 124, text: 'FlowDroid' },
    { x: 212, y: 130, text: 'Semgrep CE' },
    { x: 222, y: 128, text: 'Infer' },
  ];
  const placed = boxes(cluster);
  for (let a = 0; a < placed.length; a += 1) {
    for (let b = a + 1; b < placed.length; b += 1) {
      const overlaps =
        placed[a].left < placed[b].right &&
        placed[b].left < placed[a].right &&
        placed[a].top < placed[b].bottom &&
        placed[b].top < placed[a].bottom;
      assert.equal(overlaps, false, `${cluster[a].text} overlaps ${cluster[b].text}`);
    }
  }
});

test('labels stay inside the plot', () => {
  const corners = [
    { x: 795, y: 5, text: 'Bifrost' },
    { x: 5, y: 395, text: 'Pysa' },
  ];
  for (const box of boxes(corners)) {
    assert.ok(box.left >= bounds.left && box.right <= bounds.right, 'horizontal');
    assert.ok(box.top >= bounds.top && box.bottom <= bounds.bottom, 'vertical');
  }
});

test('an isolated point keeps its label beside it', () => {
  const [label] = placeLabels([{ x: 400, y: 200, text: 'Joern' }], { bounds });
  assert.equal(label.leader, false);
  assert.equal(label.anchor, 'start');
});
