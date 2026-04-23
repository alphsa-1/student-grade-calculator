let userId = localStorage.getItem("userId");

let subjects = [];
let editId = null;

let currentQuarterNumber = null;
let currentQuarterId = null;

let assessmentState = { categories: [] };


// ================= INIT =================
window.onload = () => {
  if (!userId) {
    loginModal.style.display = "block";
    logoutButton.style.display = "none"
  } else {
     logoutButton.style.display = "block"
    loadSubjects();
  }
};


// ================= LOGIN / SIGNUP MODALS =================
function openSignup() {
  loginModal.style.display = "none";
  signupModal.style.display = "block";
}

function closeSignup() {
  signupModal.style.display = "none";
  loginModal.style.display = "block";
}


// ================= AUTH =================
async function signup() {
  const res = await fetch("/signup", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      username: signupUser.value,
      password: signupPass.value
    })
  });

  if (res.status == 200) {
    alert("Account created");
  }
  else {
    alert("User already exists!");
  }

  closeSignup();
}

async function login() {
  const res = await fetch("/login", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      username: loginUser.value,
      password: loginPass.value
    })
  });

  const data = await res.json();

  if (data.userId) {
    userId = data.userId;
    localStorage.setItem("userId", userId);

    loginModal.style.display = "none";
    logoutButton.style.display = "block";
    loadSubjects();
  } else {
    alert("Invalid login");
  }
}

function logout() {
  localStorage.clear(); // wipes all stored keys

  userId = null;
  subjects = [];
  assessmentState = { categories: [] };

  // close all modals
  loginModal.style.display = "block";
  logoutButton.style.display = "none";
  signupModal.style.display = "none";
  subjectModal.style.display = "none";
  quarterModal.style.display = "none";
  assessmentModal.style.display = "none";

  location.reload(); // optional hard reset
}


// ================= SUBJECTS =================
async function loadSubjects() {
  const res = await fetch(`/subjects/${userId}`);
  subjects = await res.json();
  renderTable();
}

function renderTable() {
  const body = document.getElementById("gradesBody");
  body.innerHTML = "";

  const rows = Math.max(5, subjects.length);

  for (let i = 0; i < rows; i++) {
    const s = subjects[i] || {};

    body.innerHTML += `
      <tr>
        <td class="clickable" onclick="editSubject(${s.id})">${s.name || ""}</td>
        <td>${s.quarter1Grade || ""}</td><td>${s.quarter2Grade || ""}</td><td>${s.quarter3Grade || ""}</td><td>${s.quarter4Grade || ""}</td>
        <td>${s.final || ""}</td>
        <td class="clickable" onclick="editSubject(${s.id})">${s.unit || ""}</td>
        <td>${s.classification || ""}</td>
      </tr>
    `;
  }
}


// ================= SUBJECT MODAL =================
function openSubjectModal() {
  editId = null;
  subjectModal.style.display = "block";
}

function editSubject(id) {
  const s = subjects.find(x => x.id === id);
  if (!s) return;

  editId = id;
  subjectInput.value = s.name;
  unitInput.value = s.unit;

  subjectModal.style.display = "block";
}

function closeSubjectModal() {
  subjectModal.style.display = "none";
}

async function saveSubject() {
  const payload = {
    name: subjectInput.value,
    unit: unitInput.value
  };
  
  const url = editId
    ? `/subjects/${userId}/${editId}`
    : `/subjects/${userId}`;

  await fetch(url, {
    method: editId ? "PUT" : "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(payload)
  });

  closeSubjectModal();
  loadSubjects();
}


// ================= QUARTER MODAL =================
async function openQuarterModal(q) {
  currentQuarterNumber = q;

  quarterModal.style.display = "block";
  quarterTitle.innerText = `Quarter ${q}`;

  const res = await fetch(`/quarters/${userId}/${q}`);
  const data = await res.json();

  renderQuarter(data);
}

function renderQuarter(data) {
  quarterBody.innerHTML = "";

  data.forEach(row => {
    quarterBody.innerHTML += `
      <tr>
        <td onclick="openAssessment('${row.id}')"
            style="cursor:pointer;color:blue;">
          ${row.name}
        </td>
        <td>${row.grade || ""}</td>
        <td>${row.passed || ""}</td>
      </tr>
    `;
  });
}

function closeQuarterModal() {
  quarterModal.style.display = "none";
  loadSubjects();
}


// ================= ASSESSMENT =================
function openAssessment(quarterId) {
  currentQuarterId = quarterId;
  
  assessmentModal.style.display = "block";
  loadAssessments();
}

async function loadAssessments() {
  const res = await fetch(`/assessments/${currentQuarterId}`);
  assessmentState = await res.json();
  renderAssessment();
}

function renderAssessment() {
  const c = assessmentContainer;
  c.innerHTML = "";

  // ADD CATEGORY BUTTON
  c.innerHTML += `<button onclick="addCategory()">+ Add Category</button><hr>`;

  assessmentState.categories.forEach(cat => {
    c.innerHTML += `
      <div class="box">
        <b>
          ${cat.type} (${cat.percentage}%)
          <button onclick="editCategory(${cat.id})">Edit</button>
          <button onclick="deleteCategory(${cat.id})">Delete</button>
          <button onclick="addSubCategory(${cat.id})">+ Sub</button>
        </b>

        ${cat.sub_categories.map(sc => `
          <div style="margin-left:20px;">
            <b>
              ${sc.label} (${sc.percentage}%)
              <button onclick="editSubCategory(${sc.id})">Edit</button>
              <button onclick="deleteSubCategory(${sc.id})">Delete</button>
              <button onclick="addItem(${sc.id})">+ Item</button>
            </b>

            ${sc.items.map(it => `
              <div style="margin-left:20px;">
                ${it.label} ${it.score_obtained} / ${it.maximum_score}
                <button onclick="editItem(${it.id})">Edit</button>
                <button onclick="deleteItem(${it.id})">Delete</button>
              </div>
            `).join("")}
          </div>
        `).join("")}
      </div>
    `;
  });
}


// ================= ADD FUNCTIONS =================
function addCategory() {
  assessmentState.categories.push({
    id: Date.now(),
    type: prompt("Type"),
    percentage: parseFloat(prompt("Percentage")),
    sub_categories: []
  });

  renderAssessment();
}

function addSubCategory(catId) {
  const cat = assessmentState.categories.find(c => c.id === catId);

  cat.sub_categories.push({
    id: Date.now(),
    label: prompt("Label"),
    percentage: parseFloat(prompt("Percentage")),
    items: []
  });

  renderAssessment();
}

function addItem(subId) {
  for (const cat of assessmentState.categories) {
    const sub = cat.sub_categories.find(s => s.id === subId);

    if (sub) {
      sub.items.push({
        id: Date.now(),
        label: prompt("Label"),
        score_obtained: parseFloat(prompt("Score")),
        maximum_score: parseFloat(prompt("Max score"))
      });

      renderAssessment();
      return;
    }
  }
}


// ================= EDIT FUNCTIONS =================
function editCategory(id) {
  const c = assessmentState.categories.find(x => x.id === id);

  c.type = prompt("Type", c.type);
  c.percentage = parseFloat(prompt("Percent", c.percentage));

  renderAssessment();
}

function editSubCategory(id) {
  for (const c of assessmentState.categories) {
    const s = c.sub_categories.find(x => x.id === id);
    if (!s) continue;

    s.label = prompt("Label", s.label);
    s.percentage = parseFloat(prompt("Percent", s.percentage));

    renderAssessment();
    return;
  }
}

function editItem(id) {
  for (const c of assessmentState.categories) {
    for (const s of c.sub_categories) {
      const i = s.items.find(x => x.id === id);

      if (!i) continue;

      i.label = prompt("Label", i.label);
      i.score_obtained = parseFloat(prompt("Score", i.score_obtained));
      i.maximum_score = parseFloat(prompt("Max", i.maximum_score));

      renderAssessment();
      return;
    }
  }
}


// ================= DELETE FUNCTIONS =================
function deleteCategory(id) {
  assessmentState.categories =
    assessmentState.categories.filter(c => c.id !== id);

  renderAssessment();
}

function deleteSubCategory(id) {
  for (const c of assessmentState.categories) {
    c.sub_categories =
      c.sub_categories.filter(s => s.id !== id);
  }

  renderAssessment();
}

function deleteItem(id) {
  for (const c of assessmentState.categories) {
    for (const s of c.sub_categories) {
      s.items = s.items.filter(i => i.id !== id);
    }
  }

  renderAssessment();
}

function closeAssessment() {
  assessmentModal.style.display = "none";
  openQuarterModal(currentQuarterNumber);
}


// ================= CALCULATE =================
async function calculateQuarter() {
  const res = await fetch("/calculate", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({
      quarterId: currentQuarterId,
      categories: assessmentState.categories
    })
  });

  if (res.status == 200) {
    alert("Success");
    closeAssessment();
  } else {
    alert("Calculate failed!");
  }
}