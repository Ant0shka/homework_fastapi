const tokenKey = "token";

const username = document.getElementById("username");
const password = document.getElementById("password");
const loginBtn = document.getElementById("login-btn");
const registerBtn = document.getElementById("register-btn");
const logoutBtn = document.getElementById("logout-btn");
const authStatus = document.getElementById("auth-status");
const tasksBlock = document.getElementById("tasks-block");
const tasksList = document.getElementById("tasks-list");
const taskCount = document.getElementById("task-count");
const taskForm = document.getElementById("task-form");
const taskId = document.getElementById("task-id");
const taskTitle = document.getElementById("task-title");
const taskDescription = document.getElementById("task-description");
const taskStatus = document.getElementById("task-status");
const taskPriority = document.getElementById("task-priority");
const cancelEditBtn = document.getElementById("cancel-edit-btn");
const saveBtn = document.getElementById("save-btn");
const searchInput = document.getElementById("search-input");
const sortBy = document.getElementById("sort-by");
const sortOrder = document.getElementById("sort-order");
const refreshBtn = document.getElementById("refresh-btn");

function getToken() {
  return localStorage.getItem(tokenKey);
}

function setToken(value) {
  if (value) localStorage.setItem(tokenKey, value);
  else localStorage.removeItem(tokenKey);
}

function setStatus(text, ok) {
  authStatus.textContent = text || "";
  authStatus.className = "msg" + (ok ? " ok" : "");
}

async function api(path, options = {}) {
  const headers = options.headers || {};
  const token = getToken();
  if (token) headers.Authorization = "Bearer " + token;
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(path, { ...options, headers });
  if (!res.ok) {
    let msg = res.statusText;
    try {
      const data = await res.json();
      msg = data.detail || JSON.stringify(data);
    } catch (e) {}
    throw new Error(msg);
  }
  if (res.status === 204) return null;
  return res.json();
}

function showTasks(show) {
  tasksBlock.hidden = !show;
  logoutBtn.hidden = !show;
  loginBtn.hidden = show;
  registerBtn.hidden = show;
}

function resetForm() {
  taskId.value = "";
  taskForm.reset();
  taskPriority.value = "0";
  cancelEditBtn.hidden = true;
  saveBtn.textContent = "сохранить";
}

function statusClass(status) {
  if (status === "in_progress") return "in_progress";
  if (status === "completed") return "completed";
  return "pending";
}

function renderTasks(items) {
  tasksList.innerHTML = "";
  taskCount.textContent = String(items.length);

  if (!items.length) {
    tasksList.innerHTML = '<li class="empty">задач нет</li>';
    return;
  }

  for (const task of items) {
    const li = document.createElement("li");
    li.className = "task-item";

    const top = document.createElement("div");
    top.className = "task-top";

    const main = document.createElement("div");
    const title = document.createElement("h3");
    title.className = "task-title";
    title.textContent = task.title;
    main.appendChild(title);

    if (task.description) {
      const desc = document.createElement("p");
      desc.className = "task-desc";
      desc.textContent = task.description;
      main.appendChild(desc);
    }

    const tags = document.createElement("div");
    tags.className = "task-tags";
    tags.innerHTML =
      '<span class="tag ' + statusClass(task.status) + '">' +
      (task.status_label || task.status) +
      "</span>" +
      '<span class="tag">приоритет ' + task.priority + "</span>" +
      '<span class="tag">#' + task.id + "</span>";

    const actions = document.createElement("div");
    actions.className = "task-actions";

    const editBtn = document.createElement("button");
    editBtn.className = "btn small";
    editBtn.textContent = "изменить";
    editBtn.onclick = () => {
      taskId.value = task.id;
      taskTitle.value = task.title;
      taskDescription.value = task.description || "";
      taskStatus.value = task.status;
      taskPriority.value = task.priority;
      cancelEditBtn.hidden = false;
      saveBtn.textContent = "обновить";
      taskTitle.focus();
    };

    const delBtn = document.createElement("button");
    delBtn.className = "btn small danger";
    delBtn.textContent = "удалить";
    delBtn.onclick = async () => {
      if (!confirm("удалить «" + task.title + "»?")) return;
      await api("/tasks/" + task.id, { method: "DELETE" });
      await loadTasks();
    };

    actions.appendChild(editBtn);
    actions.appendChild(delBtn);
    top.appendChild(main);
    top.appendChild(actions);
    li.appendChild(top);
    li.appendChild(tags);
    tasksList.appendChild(li);
  }
}

async function loadTasks() {
  const q = searchInput.value.trim();
  let path;
  if (q) {
    path = "/tasks/search?q=" + encodeURIComponent(q);
  } else {
    path =
      "/tasks?sort_by=" +
      sortBy.value +
      "&order=" +
      sortOrder.value;
  }
  renderTasks(await api(path));
}

loginBtn.onclick = async () => {
  try {
    const body = new FormData();
    body.append("username", username.value.trim());
    body.append("password", password.value);
    const data = await api("/auth/login", { method: "POST", body });
    setToken(data.access_token);
    setStatus("", true);
    showTasks(true);
    await loadTasks();
  } catch (e) {
    setStatus(e.message);
  }
};

registerBtn.onclick = async () => {
  try {
    await api("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        username: username.value.trim(),
        password: password.value,
      }),
    });
    setStatus("ок, входим...", true);
    await loginBtn.onclick();
  } catch (e) {
    setStatus(e.message);
  }
};

logoutBtn.onclick = () => {
  setToken(null);
  showTasks(false);
  tasksList.innerHTML = "";
  resetForm();
  setStatus("");
};

refreshBtn.onclick = () => loadTasks().catch((e) => setStatus(e.message));
cancelEditBtn.onclick = resetForm;
searchInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    e.preventDefault();
    loadTasks().catch((err) => setStatus(err.message));
  }
});
sortBy.onchange = () => loadTasks().catch((e) => setStatus(e.message));
sortOrder.onchange = () => loadTasks().catch((e) => setStatus(e.message));

taskForm.onsubmit = async (e) => {
  e.preventDefault();
  const payload = {
    title: taskTitle.value.trim(),
    description: taskDescription.value.trim(),
    status: taskStatus.value,
    priority: Number(taskPriority.value),
  };

  try {
    if (taskId.value) {
      await api("/tasks/" + taskId.value, {
        method: "PATCH",
        body: JSON.stringify(payload),
      });
    } else {
      await api("/tasks", { method: "POST", body: JSON.stringify(payload) });
    }
    resetForm();
    await loadTasks();
  } catch (err) {
    setStatus(err.message);
  }
};

if (getToken()) {
  showTasks(true);
  loadTasks().catch(() => logoutBtn.onclick());
} else {
  showTasks(false);
}
