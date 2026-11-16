"use strict";

const $ = (selector) => document.querySelector(selector);
const form = $("#cv-form");
const runSelect = $("#run-select");
const textInput = $("#cv-text");
const skillsInput = $("#cv-skills");
const analyzeButton = $("#analyze-button");
const exportButton = $("#export-button");
const formatter = new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 2 });
let models = [];
let lastResult = null;
let busy = false;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function errorMessage(message = "") {
  $("#form-error").textContent = message;
  $("#form-error").hidden = !message;
}

async function request(url, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 90000);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Yêu cầu chưa thực hiện được. Vui lòng thử lại.");
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("Phân tích mất quá nhiều thời gian. Vui lòng thử lại với CV ngắn hơn.");
    if (error instanceof TypeError) throw new Error("Không kết nối được máy chủ. Hãy kiểm tra chương trình web đang chạy.");
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

function invalidate() {
  lastResult = null;
  exportButton.disabled = true;
  $("#results-content").hidden = true;
  $("#empty-state").hidden = false;
  $("#character-count").textContent = `${formatter.format(textInput.value.length)} ký tự`;
  errorMessage();
}

function selectTab(name, focus = false) {
  for (const item of ["text", "file"]) {
    const button = $(`#${item}-tab`);
    const active = item === name;
    button.classList.toggle("active", active);
    button.setAttribute("aria-selected", String(active));
    button.tabIndex = active ? 0 : -1;
    $(`#${item}-panel`).hidden = !active;
    if (active && focus) button.focus();
  }
}

for (const name of ["text", "file"]) {
  $(`#${name}-tab`).addEventListener("click", () => selectTab(name));
  $(`#${name}-tab`).addEventListener("keydown", (event) => {
    if (["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      const next = event.key === "Home" ? "text" : event.key === "End" ? "file" : name === "text" ? "file" : "text";
      selectTab(next, true);
    }
  });
}

function updateModel() {
  const model = models.find((item) => item.id === runSelect.value);
  if (!model) return;
  $("#cv-count").textContent = formatter.format(model.cv_count);
  $("#job-count").textContent = formatter.format(model.job_count);
  const demo = model.dataset_kind === "synthetic_demo";
  $("#dataset-badge").textContent = demo ? "Dữ liệu demo" : model.has_weak_labels ? "Có nhãn tự động" : "Mô hình đã lưu";
  $("#dataset-badge").classList.toggle("real", !demo && !model.has_weak_labels);
  const notice = $("#dataset-notice");
  notice.hidden = false;
  notice.textContent = demo
    ? "Đang dùng dữ liệu giả lập. Kết quả chỉ để thử chương trình, chưa đánh giá độ phù hợp thực tế."
    : model.has_weak_labels
      ? "Mô hình có sử dụng nhãn tự động. Cần đối chiếu kết quả với đánh giá độc lập của con người."
      : "Kết quả dựa trên mô hình đã huấn luyện của nhóm và danh mục vị trí hiện có.";
  invalidate();
}

async function loadModels() {
  try {
    ({ models } = await request("/api/models"));
    runSelect.replaceChildren();
    if (!models.length) {
      runSelect.append(element("option", "", "Chưa có mô hình"));
      $("#dataset-badge").textContent = "Chưa sẵn sàng";
      errorMessage("Chưa tìm thấy mô hình đã huấn luyện trong thư mục runs. Hãy tạo mô hình theo README rồi tải lại trang.");
      return;
    }
    for (const model of models) {
      const option = element("option", "", model.id);
      option.value = model.id;
      runSelect.append(option);
    }
    runSelect.disabled = false;
    analyzeButton.disabled = false;
    updateModel();
  } catch (error) {
    $("#dataset-badge").textContent = "Chưa kết nối";
    errorMessage(error.message);
  }
}

function setBusy(value) {
  busy = value;
  for (const control of form.elements) control.disabled = value;
  runSelect.disabled = value || !models.length;
  analyzeButton.disabled = value || !models.length;
  exportButton.disabled = value || !lastResult;
  $("#analyze-label").textContent = value ? "Đang phân tích…" : "Phân tích CV";
  $(".spinner").hidden = !value;
  $(".button-arrow").hidden = value;
  $("#loading-state").hidden = !value;
  $(".results-panel").setAttribute("aria-busy", String(value));
}

function tags(container, values, missing = false) {
  container.replaceChildren();
  for (const value of values) container.append(element("span", missing ? "tag missing" : "tag", value));
}

function skillList(value) {
  return (value || "").split(";").map((part) => part.trim()).filter(Boolean);
}

function renderResult(result) {
  lastResult = result;
  $("#empty-state").hidden = true;
  $("#results-content").hidden = false;
  const recognized = result.recognized_skills;
  $("#skill-count").textContent = String(recognized.length);
  tags($("#recognized-skills"), recognized.length ? recognized : ["Chưa nhận diện được kỹ năng"]);
  const unknown = result.unknown_graph_skills;
  $("#unknown-skills").hidden = !unknown.length;
  $("#unknown-skills").textContent = unknown.length ? `Kỹ năng chưa có trong mô hình: ${unknown.join(", ")}.` : "";
  $("#result-summary").textContent = `${result.ranked_jobs.length} vị trí · Sắp xếp theo điểm của mô hình`;
  const container = $("#job-results");
  container.replaceChildren();
  result.ranked_jobs.forEach((job, index) => {
    const card = element("article", "job-card");
    const top = element("div", "job-top");
    top.append(element("span", "job-rank", String(index + 1).padStart(2, "0")));
    const info = element("div", "job-info");
    info.append(element("h3", "", job.jd_title || job.jd_id), element("span", "job-id", `Vị trí · ${job.jd_id}`));
    const label = { high: "Dự đoán: Cao", medium: "Dự đoán: Trung bình", low: "Dự đoán: Thấp" }[job.predicted_label] || "Chưa xác định";
    const level = ["high", "medium", "low"].includes(job.predicted_label) ? job.predicted_label : "low";
    top.append(info, element("span", `level-badge ${level}`, label));
    const score = element("div", "score-row");
    const meter = element("meter");
    meter.min = 0;
    meter.max = 100;
    meter.value = Math.max(0, Math.min(100, Number(job.ranking_score)));
    meter.setAttribute("aria-label", `Điểm xếp hạng ${formatter.format(job.ranking_score)} trên 100`);
    const scoreText = element("span", "score-value", formatter.format(job.ranking_score));
    scoreText.append(element("small", "", "/100"));
    score.append(meter, scoreText);
    card.append(top, score, element("div", "skill-label", "KỸ NĂNG TRÙNG KHỚP"));
    const matched = skillList(job.matched_skills);
    const matches = element("div", "tags");
    if (matched.length) tags(matches, matched);
    else matches.append(element("p", "no-skills", "Chưa tìm thấy kỹ năng trùng trong danh sách."));
    card.append(matches);
    const missing = skillList(job.missing_skills);
    const details = element("details");
    details.append(element("summary", "", missing.length ? `${missing.length} kỹ năng cần bổ sung` : "Đã có các kỹ năng trong danh sách yêu cầu"));
    const gaps = element("div", "tags");
    tags(gaps, missing.length ? missing : ["Không có kỹ năng thiếu trong danh sách"], missing.length > 0);
    details.append(gaps);
    card.append(details);
    container.append(card);
  });
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (busy || !models.length) return;
  if (!textInput.value.trim()) {
    errorMessage("Bạn hãy nhập nội dung CV hoặc chọn “Dùng CV mẫu” để thử.");
    selectTab("text");
    textInput.focus();
    return;
  }
  invalidate();
  $("#empty-state").hidden = true;
  const payload = { run_id: runSelect.value, cv_text: textInput.value, top_k: Number($("#top-k").value) };
  if (skillsInput.value.trim()) payload.cv_skills = skillsInput.value.split(/[,;\n]+/).map((part) => part.trim()).filter(Boolean);
  setBusy(true);
  try {
    const result = await request("/api/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    renderResult(result);
    if (matchMedia("(max-width: 760px)").matches) $(".results-panel").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    errorMessage(error.message);
    $("#empty-state").hidden = false;
  } finally {
    setBusy(false);
  }
});

$("#sample-button").addEventListener("click", async () => {
  try {
    const sample = await request("/api/sample");
    textInput.value = sample.cv_text;
    skillsInput.value = sample.cv_skills.join(", ");
    $("#file-status").hidden = true;
    $("#cv-file").value = "";
    invalidate();
    textInput.focus();
  } catch (error) { errorMessage(error.message); }
});

async function loadFile(file) {
  if (!file || busy) return;
  try {
    if (file.size > 1048576) throw new Error("Tệp vượt quá 1 MB. Hãy dùng tệp văn bản ngắn hơn.");
    const extension = file.name.split(".").pop().toLowerCase();
    if (!["txt", "json"].includes(extension)) throw new Error("Hiện hỗ trợ TXT và JSON. Với PDF, hãy sao chép phần văn bản vào ô nhập CV.");
    const content = (await file.text()).replace(/^\uFEFF/, "");
    let record = { cv_text: content };
    if (extension === "json") {
      try { record = JSON.parse(content); }
      catch { throw new Error("Không đọc được JSON. Kiểm tra dấu ngoặc, dấu nháy và trường cv_text."); }
    }
    if (!record || typeof record.cv_text !== "string" || !record.cv_text.trim()) throw new Error("Tệp cần chứa nội dung CV. JSON phải có trường cv_text là văn bản.");
    if (record.cv_text.length > 100000) throw new Error("Nội dung CV vượt quá 100.000 ký tự.");
    const supplied = record.cv_skills;
    if (supplied != null && typeof supplied !== "string" && !(Array.isArray(supplied) && supplied.every((item) => typeof item === "string"))) throw new Error("cv_skills phải là danh sách kỹ năng hoặc chuỗi văn bản.");
    textInput.value = record.cv_text;
    skillsInput.value = Array.isArray(supplied) ? supplied.join(", ") : supplied || "";
    $("#file-status").textContent = `Đã đọc ${file.name} · Bạn có thể chỉnh sửa nội dung bên dưới.`;
    $("#file-status").hidden = false;
    selectTab("text");
    invalidate();
  } catch (error) { errorMessage(error.message); }
}

$("#cv-file").addEventListener("change", (event) => loadFile(event.target.files[0]));
const dropZone = $("#drop-zone");
for (const eventName of ["dragenter", "dragover"]) dropZone.addEventListener(eventName, (event) => {
  event.preventDefault();
  if (!busy) dropZone.classList.add("dragging");
});
for (const eventName of ["dragleave", "drop"]) dropZone.addEventListener(eventName, (event) => {
  event.preventDefault();
  dropZone.classList.remove("dragging");
  if (eventName === "drop") loadFile(event.dataTransfer.files[0]);
});

exportButton.addEventListener("click", () => {
  if (!lastResult) return;
  const fields = ["jd_id", "jd_title", "ranking_score", "predicted_label", "matched_skills", "missing_skills"];
  function cell(value) {
    let text = String(value ?? "");
    if (/^[\s]*[=+\-@]/.test(text)) text = `'${text}`;
    return `"${text.replaceAll('"', '""')}"`;
  }
  const csv = "\uFEFF" + [fields.map(cell).join(","), ...lastResult.ranked_jobs.map((job) => fields.map((field) => cell(job[field])).join(","))].join("\r\n");
  const url = URL.createObjectURL(new Blob([csv], { type: "text/csv;charset=utf-8;" }));
  const link = element("a");
  link.href = url;
  link.download = "cvmatch-ket-qua.csv";
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

textInput.addEventListener("input", invalidate);
skillsInput.addEventListener("input", invalidate);
$("#top-k").addEventListener("change", invalidate);
runSelect.addEventListener("change", updateModel);
textInput.addEventListener("keydown", (event) => {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") { event.preventDefault(); form.requestSubmit(); }
});
const help = $("#help-dialog");
$("#help-button").addEventListener("click", () => help.showModal());
$("#close-help").addEventListener("click", () => help.close());
$("#help-done").addEventListener("click", () => { help.close(); textInput.focus(); });
help.addEventListener("click", (event) => {
  const rect = help.getBoundingClientRect();
  if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) help.close();
});

loadModels();
