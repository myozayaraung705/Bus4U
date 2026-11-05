(function (root, factory) {
  const api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else root.Bus4USheet = api;
})(typeof window === "object" ? window : globalThis, function () {
  "use strict";

  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const states = ["minimized", "default", "expanded"];

  function chooseSnapState(height, velocity, points) {
    const projected = clamp(height + clamp(velocity, -2.5, 2.5) * 160, points.minimized, points.expanded);
    return states.reduce((nearest, name) =>
      Math.abs(points[name] - projected) < Math.abs(points[nearest] - projected) ? name : nearest,
    "minimized");
  }

  function createController({ panel, handle, content, getSnapPoints, isEnabled, onStateChange = () => {} }) {
    let currentState = "default";
    let gesture = null;
    let suppressClick = false;
    const ownerWindow = panel.ownerDocument.defaultView;

    function applyState(nextState) {
      currentState = states.includes(nextState) ? nextState : "default";
      panel.classList.toggle("is-collapsed", currentState === "minimized");
      panel.classList.toggle("is-expanded", currentState === "expanded");
      panel.dataset.sheetState = currentState;
      content.inert = currentState === "minimized";
      content.setAttribute("aria-hidden", String(currentState === "minimized"));
      handle.setAttribute("aria-expanded", String(currentState !== "minimized"));
      onStateChange(currentState);
    }

    function clearDrag() {
      const previous = gesture;
      gesture = null;
      panel.classList.remove("is-dragging");
      panel.style.removeProperty("height");
      handle.removeAttribute("data-dragging");
      if (previous && handle.hasPointerCapture(previous.id)) handle.releasePointerCapture(previous.id);
      return previous;
    }

    function setState(nextState) {
      clearDrag();
      applyState(nextState);
    }

    function addSample(event) {
      gesture.samples.push({ y: event.clientY, time: event.timeStamp });
      gesture.samples = gesture.samples.filter((sample) => event.timeStamp - sample.time <= 100);
    }

    function pointerDown(event) {
      if (!isEnabled() || gesture || event.isPrimary === false || (event.pointerType === "mouse" && event.button !== 0)) return;
      suppressClick = false;
      const points = getSnapPoints();
      gesture = {
        id: event.pointerId,
        startX: event.clientX,
        startY: event.clientY,
        startHeight: panel.getBoundingClientRect().height,
        startState: currentState,
        height: panel.getBoundingClientRect().height,
        points,
        moved: false,
        samples: [{ y: event.clientY, time: event.timeStamp }]
      };
      handle.setPointerCapture(event.pointerId);
    }

    function pointerMove(event) {
      if (!gesture || event.pointerId !== gesture.id) return;
      const deltaY = gesture.startY - event.clientY;
      if (!gesture.moved) {
        if (Math.abs(deltaY) < 6 || Math.abs(deltaY) < Math.abs(event.clientX - gesture.startX)) return;
        gesture.moved = true;
        panel.classList.add("is-dragging");
        panel.classList.remove("is-collapsed");
        panel.style.height = `${gesture.startHeight}px`;
        content.inert = false;
        content.setAttribute("aria-hidden", "false");
        handle.setAttribute("data-dragging", "true");
      }
      event.preventDefault();
      gesture.height = clamp(gesture.startHeight + deltaY, gesture.points.minimized, gesture.points.expanded);
      panel.style.height = `${gesture.height}px`;
      addSample(event);
    }

    function pointerUp(event) {
      if (!gesture || event.pointerId !== gesture.id) return;
      pointerMove(event);
      const previous = gesture;
      if (previous.moved) {
        addSample(event);
        const first = previous.samples[0];
        const elapsed = event.timeStamp - first.time;
        const velocity = elapsed > 0 ? (first.y - event.clientY) / elapsed : 0;
        const next = chooseSnapState(previous.height, velocity, previous.points);
        // Freeze the final dragged position before enabling the snap animation.
        panel.getBoundingClientRect();
        suppressClick = true;
        ownerWindow.setTimeout(() => { suppressClick = false; }, 0);
        clearDrag();
        applyState(next);
      } else {
        clearDrag();
      }
    }

    function cancelGesture(event) {
      if (!gesture || (event && event.pointerId !== gesture.id)) return;
      const previous = clearDrag();
      applyState(previous.startState);
    }

    function click(event) {
      if (!isEnabled()) return;
      if (suppressClick) {
        event.preventDefault();
        return;
      }
      setState(currentState === "minimized" ? "default" : "minimized");
    }

    function keyDown(event) {
      if (!isEnabled()) return;
      const index = states.indexOf(currentState);
      const next = {
        ArrowUp: states[Math.min(states.length - 1, index + 1)],
        ArrowDown: states[Math.max(0, index - 1)],
        Home: "minimized",
        End: "expanded",
        Escape: "minimized"
      }[event.key];
      if (!next) return;
      event.preventDefault();
      setState(next);
    }

    function resize() {
      cancelGesture();
      if (!isEnabled()) setState("default");
    }

    handle.addEventListener("pointerdown", pointerDown);
    handle.addEventListener("pointermove", pointerMove, { passive: false });
    handle.addEventListener("pointerup", pointerUp);
    handle.addEventListener("pointercancel", cancelGesture);
    handle.addEventListener("lostpointercapture", cancelGesture);
    handle.addEventListener("click", click);
    handle.addEventListener("keydown", keyDown);
    ownerWindow.addEventListener("resize", resize);
    applyState("default");

    return { setState, getState: () => currentState };
  }

  return { chooseSnapState, createController };
});
