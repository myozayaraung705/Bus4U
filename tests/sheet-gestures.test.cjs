const test = require("node:test");
const assert = require("node:assert/strict");
const { chooseSnapState, createController } = require("../sheet-gestures.js");

const points = { minimized: 56, default: 440, expanded: 746 };

function fixture() {
  const handlers = {};
  const classes = new Set();
  const attributes = new Map();
  const styles = {};
  const captured = new Set();
  const timers = [];
  const windowHandlers = {};
  let mobile = true;
  const panel = {
    dataset: {},
    ownerDocument: { defaultView: {
      setTimeout: (callback) => timers.push(callback),
      addEventListener: (type, callback) => { windowHandlers[type] = callback; }
    } },
    classList: {
      toggle(name, enabled) { if (enabled) classes.add(name); else classes.delete(name); },
      add: (name) => classes.add(name),
      remove: (name) => classes.delete(name)
    },
    style: { removeProperty: (name) => { delete styles[name]; }, set height(value) { styles.height = value; } },
    getBoundingClientRect: () => ({ height: styles.height ? parseFloat(styles.height) : points[panel.dataset.sheetState || "default"] })
  };
  const handle = {
    setAttribute: (key, value) => attributes.set(key, value),
    removeAttribute: (key) => attributes.delete(key),
    addEventListener: (type, callback) => { handlers[type] = callback; },
    setPointerCapture: (id) => captured.add(id),
    hasPointerCapture: (id) => captured.has(id),
    releasePointerCapture: (id) => { captured.delete(id); handlers.lostpointercapture?.({ pointerId: id }); }
  };
  const contentAttributes = new Map();
  const content = { setAttribute: (key, value) => contentAttributes.set(key, value) };
  const controller = createController({ panel, handle, content, getSnapPoints: () => points, isEnabled: () => mobile });
  const event = (y, time = 0, extra = {}) => ({
    clientX: 100, clientY: y, timeStamp: time, pointerId: 1, pointerType: "touch", isPrimary: true, button: 0,
    preventDefault() { this.prevented = true; }, ...extra
  });
  return { controller, panel, styles, classes, attributes, content, contentAttributes, handlers, windowHandlers, captured, timers, event, setMobile: (value) => { mobile = value; } };
}

test("slow drags snap to the nearest position; flicks use their direction", () => {
  assert.equal(chooseSnapState(90, 0, points), "minimized");
  assert.equal(chooseSnapState(400, 0, points), "default");
  assert.equal(chooseSnapState(690, 0, points), "expanded");
  assert.equal(chooseSnapState(420, 1.5, points), "expanded");
  assert.equal(chooseSnapState(350, -1.5, points), "minimized");
});

test("a touch drag follows the finger, closes the sheet, and keeps the handle operable", () => {
  const f = fixture();
  f.handlers.pointerdown(f.event(300));
  f.handlers.pointermove(f.event(650, 500));
  assert.equal(f.styles.height, "90px");
  assert.ok(f.classes.has("is-dragging"));
  f.handlers.pointerup(f.event(650, 700));
  assert.equal(f.controller.getState(), "minimized");
  assert.equal(f.attributes.get("aria-expanded"), "false");
  assert.equal(f.content.inert, true);
  assert.equal(f.styles.height, undefined);
  assert.equal(f.captured.size, 0);
  f.handlers.click(f.event(650));
  assert.equal(f.controller.getState(), "minimized", "a drag must not also trigger a tap");
  f.timers.forEach((callback) => callback());
  f.handlers.click(f.event(650));
  assert.equal(f.controller.getState(), "default");
});

test("the closed handle can be held and dragged up to expand", () => {
  const f = fixture();
  f.controller.setState("minimized");
  f.handlers.pointerdown(f.event(740));
  f.handlers.pointermove(f.event(80, 600));
  assert.equal(f.styles.height, "716px");
  assert.equal(f.content.inert, false);
  f.handlers.pointerup(f.event(80, 800));
  assert.equal(f.controller.getState(), "expanded");
  assert.equal(f.attributes.get("aria-expanded"), "true");
});

test("an interrupted touch restores its original position and accessibility state", () => {
  const f = fixture();
  f.controller.setState("minimized");
  f.handlers.pointerdown(f.event(700));
  f.handlers.pointermove(f.event(400, 200));
  f.handlers.pointercancel(f.event(400, 250));
  assert.equal(f.controller.getState(), "minimized");
  assert.equal(f.styles.height, undefined);
  assert.equal(f.content.inert, true);
  assert.equal(f.classes.has("is-dragging"), false);
});

test("a second finger cannot take over an active drag", () => {
  const f = fixture();
  f.handlers.pointerdown(f.event(300));
  f.handlers.pointermove(f.event(600, 100, { pointerId: 2, isPrimary: false }));
  f.handlers.pointerup(f.event(600, 200, { pointerId: 2, isPrimary: false }));
  assert.equal(f.styles.height, undefined);
  assert.ok(f.captured.has(1));
  f.handlers.pointercancel(f.event(300, 300));
});

test("holding without dragging is still a tap, and keyboard users can resize", () => {
  const f = fixture();
  f.handlers.pointerdown(f.event(300));
  f.handlers.pointerup(f.event(302, 1000));
  f.handlers.click(f.event(302, 1000));
  assert.equal(f.controller.getState(), "minimized");
  f.handlers.keydown(f.event(0, 0, { key: "ArrowUp" }));
  assert.equal(f.controller.getState(), "default");
  f.handlers.keydown(f.event(0, 0, { key: "End" }));
  assert.equal(f.controller.getState(), "expanded");
  f.handlers.keydown(f.event(0, 0, { key: "Home" }));
  assert.equal(f.controller.getState(), "minimized");
});

test("switching to desktop cancels a gesture and restores the panel", () => {
  const f = fixture();
  f.handlers.pointerdown(f.event(300));
  f.handlers.pointermove(f.event(650, 200));
  f.setMobile(false);
  f.windowHandlers.resize();
  assert.equal(f.controller.getState(), "default");
  assert.equal(f.styles.height, undefined);
  assert.equal(f.content.inert, false);
  f.handlers.pointerdown(f.event(300));
  assert.equal(f.captured.size, 0);
});
