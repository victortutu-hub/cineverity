"use strict";

const STAGES = [
  "director",
  "research_planning",
  "parallel_retrieval",
  "research",
  "physical_constraints",
  "scene_planning",
  "validation_readiness",
];
const SPECIALIST_ARTIFACT_STAGES = [
  "director",
  "research",
  "physical_constraints",
  "scene_planning",
  "validation_readiness",
];
const STAGE_LABELS = {
  director: "Director",
  research_planning: "Research Planning",
  parallel_retrieval: "Parallel Retrieval",
  research: "Research Synthesis",
  physical_constraints: "Physical Constraints",
  scene_planning: "Scene Planning",
  validation_readiness: "Validation Readiness",
};
const FAILURE_CODES = ["stage_failed", "internal_error", "run_timeout"];
const SAMPLE_BRIEF = "A faceted crystal rests on wet black stone at dusk. Low cyan light enters from camera-left, separates through the crystal, and casts restrained caustic patterns across the surface. Preserve an intentional cinematic amplification while identifying what remains physically grounded and what requires explicit artistic acceptance.";

const form = document.querySelector("#brief-form");
const brief = document.querySelector("#brief");
const counter = document.querySelector("#brief-counter");
const submitButton = document.querySelector("#run-button");
const sampleButton = document.querySelector("#sample-brief");
const stageRail = document.querySelector("#stage-rail");
const artifactGrid = document.querySelector("#artifact-grid");
const runIdElement = document.querySelector("#run-id");
const terminalStatus = document.querySelector("#terminal-status");
const workspace = document.querySelector(".console");
const stageStates = new Map();
const stageElements = new Map();
const artifactElements = new Map();

class ProtocolError extends Error {}

function setTerminal(kind, message) {
  terminalStatus.className = `terminal-status ${kind}`;
  terminalStatus.textContent = message;
}

function updateCounter() {
  counter.textContent = `${brief.value.length} / 6000`;
}

function renderStages() {
  stageRail.replaceChildren();
  STAGES.forEach((stage) => {
    const item = document.createElement("li");
    item.className = "stage pending";
    const label = document.createElement("span");
    label.textContent = STAGE_LABELS[stage];
    const state = document.createElement("span");
    state.className = "stage-state";
    state.textContent = "pending";
    item.append(label, state);
    stageRail.append(item);
    stageElements.set(stage, { item, state });
  });
}

function renderArtifactPanels() {
  artifactGrid.replaceChildren();
  SPECIALIST_ARTIFACT_STAGES.forEach((stage) => {
    const panel = document.createElement("article");
    panel.className = "artifact";
    const heading = document.createElement("h3");
    heading.textContent = STAGE_LABELS[stage];
    const content = document.createElement("pre");
    content.className = "placeholder";
    content.textContent = "Awaiting accepted artifact.";
    panel.append(heading, content);
    artifactGrid.append(panel);
    artifactElements.set(stage, content);
  });
}

function resetRunView() {
  stageStates.clear();
  STAGES.forEach((stage) => {
    stageStates.set(stage, "pending");
    const element = stageElements.get(stage);
    element.item.className = "stage pending";
    element.state.textContent = "pending";
  });
  artifactElements.forEach((content) => {
    content.className = "placeholder";
    content.textContent = "Awaiting accepted artifact.";
  });
  runIdElement.textContent = "Awaiting server-owned run identity.";
}

function setStageState(stage, nextState) {
  const currentState = stageStates.get(stage);
  if (!STAGES.includes(stage) || currentState === undefined) {
    throw new ProtocolError("Unknown pipeline stage.");
  }
  if (nextState === "running" && currentState !== "pending") {
    throw new ProtocolError("Invalid stage start transition.");
  }
  if (nextState === "accepted" && currentState !== "running") {
    throw new ProtocolError("Invalid stage acceptance transition.");
  }
  if (nextState === "failed" && currentState !== "running") {
    throw new ProtocolError("Invalid stage failure transition.");
  }
  stageStates.set(stage, nextState);
  const element = stageElements.get(stage);
  element.item.className = `stage ${nextState}`;
  element.state.textContent = nextState;
}

function renderArtifact(stage, artifact) {
  const content = artifactElements.get(stage);
  if (!content) {
    throw new ProtocolError("Internal stage artifact is not permitted.");
  }
  content.className = "";
  content.textContent = JSON.stringify(artifact, null, 2);
}

function setActive(active) {
  submitButton.disabled = active;
  sampleButton.disabled = active;
  brief.disabled = active;
  workspace.setAttribute("aria-busy", String(active));
}

function localFailure(message) {
  setTerminal("failed", message);
}

function parseErrorStatus(status) {
  if (status === 422) return ["failed", "The brief was rejected by the request boundary."];
  if (status === 415) return ["failed", "The browser request protocol was rejected."];
  if (status === 429) return ["busy", "Another run is active, or a timed-out run is still draining safely. Retry manually later."];
  if (status === 503) return ["failed", "Hosted runtime configuration is unavailable."];
  if (status === 500) return ["failed", "The hosted runtime could not start the run."];
  return ["failed", "The hosted service returned an unexpected response."];
}

function requireRunId(event, runId) {
  if (typeof event.run_id !== "string" || event.run_id.length === 0) {
    throw new ProtocolError("Missing server run identity.");
  }
  if (runId !== event.run_id) {
    throw new ProtocolError("Run identity changed during the stream.");
  }
}

function processEvent(event, state) {
  if (!event || typeof event !== "object" || typeof event.type !== "string") {
    throw new ProtocolError("Malformed NDJSON event.");
  }
  if (state.eventCount === 0 && event.type !== "run_started") {
    throw new ProtocolError("The stream did not begin with run_started.");
  }
  state.eventCount += 1;
  if (state.terminal) {
    throw new ProtocolError("Event received after terminal state.");
  }
  if (event.type === "run_started") {
    if (state.runId !== null) throw new ProtocolError("Duplicate run_started event.");
    if (typeof event.run_id !== "string" || event.run_id.length === 0) throw new ProtocolError("Missing server run identity.");
    state.runId = event.run_id;
    runIdElement.textContent = event.run_id;
    setTerminal("", "Run started. Waiting for hosted stage events.");
    return;
  }
  if (state.runId === null) throw new ProtocolError("Event received before run_started.");
  requireRunId(event, state.runId);
  if (state.pendingFailure && event.type !== "run_failed") {
    throw new ProtocolError("Event received after a server failure.");
  }
  if (event.type === "stage_started") {
    if (
      state.activeStage !== null ||
      state.nextStageIndex >= STAGES.length ||
      event.stage !== STAGES[state.nextStageIndex]
    ) {
      throw new ProtocolError("Out-of-order stage start.");
    }
    setStageState(event.stage, "running");
    state.activeStage = event.stage;
    return;
  }
  if (event.type === "stage_accepted") {
    if (event.stage !== state.activeStage) {
      throw new ProtocolError("Stage acceptance does not match the active stage.");
    }
    if (SPECIALIST_ARTIFACT_STAGES.includes(event.stage)) {
      if (!("artifact" in event) || event.artifact === null || typeof event.artifact !== "object") {
        throw new ProtocolError("Specialist acceptance lacks an artifact.");
      }
    } else if ("artifact" in event) {
      throw new ProtocolError("Internal stage artifact is not permitted.");
    }
    setStageState(event.stage, "accepted");
    if (SPECIALIST_ARTIFACT_STAGES.includes(event.stage)) renderArtifact(event.stage, event.artifact);
    state.activeStage = null;
    state.nextStageIndex += 1;
    return;
  }
  if (event.type === "stage_failed") {
    if (!event.error || !FAILURE_CODES.includes(event.error.code)) {
      throw new ProtocolError("Unknown failure code.");
    }
    if (event.stage === "internal") {
      if (event.error.code !== "internal_error") throw new ProtocolError("Invalid internal failure marker.");
    } else {
      if (event.stage !== state.activeStage) {
        throw new ProtocolError("Stage failure does not match the active stage.");
      }
      setStageState(event.stage, "failed");
      state.activeStage = null;
    }
    state.pendingFailure = { stage: event.stage, code: event.error.code };
    return;
  }
  if (event.type === "run_completed") {
    if (
      state.pendingFailure ||
      state.activeStage !== null ||
      state.nextStageIndex !== STAGES.length ||
      !STAGES.every((stage) => stageStates.get(stage) === "accepted")
    ) {
      throw new ProtocolError("Run completed before the full successful stage sequence.");
    }
    state.terminal = true;
    setTerminal("completed", "Completed. Accepted artifacts are available for inspection.");
    return;
  }
  if (event.type === "run_failed") {
    if (!event.error || !FAILURE_CODES.includes(event.error.code)) throw new ProtocolError("Unknown failure code.");
    const hasStage = Object.prototype.hasOwnProperty.call(event, "stage");
    if (hasStage && !STAGES.includes(event.stage) && event.stage !== "internal") {
      throw new ProtocolError("Unknown terminal failure stage.");
    }
    if (hasStage && event.stage === "internal" && event.error.code !== "internal_error") {
      throw new ProtocolError("Invalid internal terminal failure marker.");
    }
    if (state.pendingFailure) {
      if (!hasStage || event.stage !== state.pendingFailure.stage || event.error.code !== state.pendingFailure.code) {
        throw new ProtocolError("Terminal failure does not match the recorded stage failure.");
      }
    } else if (!(event.error.code === "run_timeout" && !hasStage && state.nextStageIndex === 0 && state.activeStage === null)) {
      throw new ProtocolError("Terminal failure lacks a matching stage failure.");
    }
    state.terminal = true;
    if (event.error.code === "run_timeout") {
      setTerminal("timeout", "The run exceeded its execution deadline. Internal cleanup may still be draining safely.");
    } else {
      setTerminal("failed", event.error.message || "The hosted pipeline did not complete.");
    }
    return;
  }
  throw new ProtocolError("Unknown hosted event.");
}

async function consumeRun() {
  const response = await fetch("/api/runs", {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept": "application/x-ndjson" },
    body: JSON.stringify({ brief: brief.value }),
  });
  if (!response.ok) {
    const [kind, message] = parseErrorStatus(response.status);
    setTerminal(kind, message);
    return;
  }
  const contentType = response.headers.get("content-type") || "";
  if (!contentType.toLowerCase().startsWith("application/x-ndjson") || !response.body) {
    throw new ProtocolError("The hosted response was not an NDJSON stream.");
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  const state = { eventCount: 0, runId: null, terminal: false, nextStageIndex: 0, activeStage: null, pendingFailure: null };
  let buffer = "";
  const handleLine = (line) => {
    if (line.trim()) processEvent(JSON.parse(line), state);
  };
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let newlineIndex = buffer.indexOf("\n");
    while (newlineIndex !== -1) {
      handleLine(buffer.slice(0, newlineIndex));
      buffer = buffer.slice(newlineIndex + 1);
      newlineIndex = buffer.indexOf("\n");
    }
  }
  buffer += decoder.decode();
  if (buffer.trim()) handleLine(buffer);
  if (!state.terminal) throw new ProtocolError("The hosted stream ended before a terminal event.");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!brief.value.trim()) {
    localFailure("Enter a non-blank creative brief before starting a run.");
    return;
  }
  resetRunView();
  setActive(true);
  setTerminal("", "Submitting the brief to the hosted pipeline.");
  try {
    await consumeRun();
  } catch (error) {
    localFailure("Browser transport or protocol failure. No additional pipeline state was inferred.");
  } finally {
    setActive(false);
  }
});

sampleButton.addEventListener("click", () => {
  brief.value = SAMPLE_BRIEF;
  updateCounter();
  brief.focus();
});

brief.addEventListener("input", updateCounter);
renderStages();
renderArtifactPanels();
resetRunView();
updateCounter();
