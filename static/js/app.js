/**
 * Internal Marks Management System - Frontend Application Logic
 * Vanilla JavaScript SPA Router, REST Client, and Reactive UI Renderer
 */

// Global State
const state = {
  currentTab: 'dashboard',
  students: [],
  subjects: [],
  marks: [],
  editingStudentId: null,
  editingSubjectId: null,
  editingMarksId: null,
  sqlPresets: {}
};

// ==============================================================================
// 1. Lifecycle & Navigation
// ==============================================================================

document.addEventListener('DOMContentLoaded', () => {
  initApp();
});

async function initApp() {
  await checkDatabaseHealth();
  await loadDropdowns();
  await loadDashboardStats();
  await loadPresetQueries();
}

function switchTab(tabId) {
  state.currentTab = tabId;

  // Update nav link active state
  document.querySelectorAll('.nav-link').forEach(link => {
    link.classList.remove('active');
  });
  const activeLink = document.getElementById(`nav-${tabId}`);
  if (activeLink) activeLink.classList.add('active');

  // Update view sections visibility
  document.querySelectorAll('.view-section').forEach(sec => {
    sec.classList.remove('active');
  });
  const targetView = document.getElementById(`view-${tabId}`);
  if (targetView) targetView.classList.add('active');

  // Update Topbar Title & Subtitle
  const headings = {
    dashboard: ['Academic Dashboard Overview', 'Live aggregated metrics and performance insights from PostgreSQL'],
    students: ['Student Profile Management', 'Manage student registration records (Mapped to ER Entity: STUDENT)'],
    subjects: ['Course Curriculum Subjects', 'Maintain subjects and maximum marks check constraints'],
    marks: ['Internal Marks Allocation', 'Assign and update subject scores with upper bound trigger enforcement'],
    results: ['Academic Marksheet & Results', 'Student-level grade cards and performance distribution'],
    reports: ['SQL Analytics & Interactive Console', 'Multi-table analytical queries and faculty demonstration console'],
    viva: ['DBMS Architecture & Viva Guide', 'Conceptual schema, 3NF relational mapping, and integrity triggers']
  };

  const [title, subtitle] = headings[tabId] || ['Marks System', 'DBMS Micro-Project'];
  document.getElementById('page-heading').innerText = title;
  document.getElementById('page-subheading').innerText = subtitle;

  // Load view-specific data
  refreshCurrentView();
}

function refreshCurrentView(isManual = false) {
  if (state.currentTab === 'dashboard') {
    loadDashboardStats();
    if (isManual) showToast('Dashboard refreshed with latest PostgreSQL records', 'success');
  } else if (state.currentTab === 'students') {
    loadStudentsData();
    if (isManual) showToast('Student list refreshed', 'success');
  } else if (state.currentTab === 'subjects') {
    loadSubjectsData();
    if (isManual) showToast('Subjects refreshed', 'success');
  } else if (state.currentTab === 'marks') {
    loadDropdowns();
    loadMarksData();
    if (isManual) showToast('Marks records refreshed', 'success');
  } else if (state.currentTab === 'results') {
    loadDropdowns();
    loadStudentMarksheet();
    if (isManual) showToast('Results view refreshed', 'success');
  }
}

// ==============================================================================
// 2. Database Health & Dropdowns
// ==============================================================================

async function checkDatabaseHealth() {
  const pill = document.getElementById('db-status-pill');
  const text = document.getElementById('db-status-text');

  try {
    const res = await fetch('/api/health');
    const data = await res.json();
    if (data.success) {
      pill.style.background = 'rgba(16, 185, 129, 0.08)';
      pill.style.borderColor = 'rgba(16, 185, 129, 0.2)';
      pill.style.color = '#34D399';
      text.innerText = 'PostgreSQL: Connected (Port 3000)';
    } else {
      throw new Error(data.message || 'Offline');
    }
  } catch (err) {
    pill.style.background = 'rgba(239, 68, 68, 0.1)';
    pill.style.borderColor = 'rgba(239, 68, 68, 0.3)';
    pill.style.color = '#F87171';
    text.innerText = 'PostgreSQL: Disconnected';
  }
}

async function loadDropdowns() {
  try {
    const res = await fetch('/api/dropdowns');
    const data = await res.json();
    if (!data.success) return;

    // Student dropdown in Marks Entry
    const marksStudentSel = document.getElementById('marks-student-select');
    const resultsStudentSel = document.getElementById('results-student-select');

    const studentOpts = '<option value="">-- Choose Student --</option>' +
      data.students.map(s => `<option value="${s.student_id}">${s.display}</option>`).join('');

    if (marksStudentSel) {
      const currentVal = marksStudentSel.value;
      marksStudentSel.innerHTML = studentOpts;
      if (currentVal) marksStudentSel.value = currentVal;
    }
    if (resultsStudentSel) {
      const currentVal = resultsStudentSel.value;
      resultsStudentSel.innerHTML = studentOpts;
      if (currentVal) resultsStudentSel.value = currentVal;
    }

    // Subject dropdown in Marks Entry
    const marksSubSel = document.getElementById('marks-subject-select');
    state.subjectsList = data.subjects;
    if (marksSubSel) {
      const currentVal = marksSubSel.value;
      marksSubSel.innerHTML = '<option value="">-- Choose Subject --</option>' +
        data.subjects.map(sub => `<option value="${sub.subject_id}" data-max="${sub.max_marks}">${sub.display}</option>`).join('');
      if (currentVal) marksSubSel.value = currentVal;
    }

    // Filter by Class dropdown
    const classFilter = document.getElementById('filter-marks-class');
    if (classFilter && data.classes) {
      classFilter.innerHTML = '<option value="ALL">All Classes</option>' +
        data.classes.map(c => `<option value="${c}">${c}</option>`).join('');
    }
  } catch (e) {
    console.error('Failed to load dropdown options:', e);
  }
}

function updateMaxMarksHint() {
  const sel = document.getElementById('marks-subject-select');
  const hint = document.getElementById('marks-subject-hint');
  const opt = sel.options[sel.selectedIndex];
  if (opt && opt.dataset.max) {
    hint.innerText = `Subject maximum: ${opt.dataset.max} marks`;
  } else {
    hint.innerText = 'Subject maximum: -- marks';
  }
}

// ==============================================================================
// 3. Dashboard View Logic
// ==============================================================================

async function loadDashboardStats() {
  try {
    const res = await fetch('/api/stats');
    const json = await res.json();
    if (!json.success) return;

    const stats = json.data;
    document.getElementById('kpi-students').innerText = stats.total_students;
    document.getElementById('kpi-subjects').innerText = stats.total_subjects;
    document.getElementById('kpi-marks-records').innerText = stats.total_marks_records;
    document.getElementById('kpi-assessed').innerText = stats.students_with_marks;
    document.getElementById('kpi-unmarked').innerText = stats.students_without_marks;
    document.getElementById('kpi-avg-pct').innerText = `${stats.overall_average_percentage}%`;

    // 1. Render Recently Registered Students Table
    const tbodyStudents = document.getElementById('tbody-recent-students');
    if (tbodyStudents) {
      if (!stats.recent_students || stats.recent_students.length === 0) {
        tbodyStudents.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-dim); padding: 30px;">No registered students found.</td></tr>`;
      } else {
        tbodyStudents.innerHTML = stats.recent_students.map(s => {
          const mCount = parseInt(s.marks_count || 0);
          const badgeClass = mCount > 0 ? 'badge-distinction' : 'badge-second';
          const badgeText = mCount > 0 ? `✓ Graded (${mCount})` : '⚠️ Pending Marks';
          return `
            <tr>
              <td style="text-align: center; color: var(--text-dim); font-family: var(--font-mono);">${s.student_id}</td>
              <td style="font-weight: 600; color: #FFF;">${escapeHtml(s.name)}</td>
              <td style="text-align: center;"><span class="badge" style="background: rgba(255,255,255,0.06);">${escapeHtml(s.roll_no)}</span></td>
              <td style="text-align: center; color: var(--text-muted);">${escapeHtml(s.class_name)} - ${escapeHtml(s.division)}</td>
              <td style="text-align: center;"><span class="badge ${badgeClass}">${badgeText}</span></td>
            </tr>
          `;
        }).join('');
      }
    }

    // 2. Render Recent Marks Stream Table
    const tbodyMarks = document.getElementById('tbody-recent-marks');
    if (tbodyMarks) {
      if (!stats.recent_marks || stats.recent_marks.length === 0) {
        tbodyMarks.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-dim); padding: 30px;">No marks recorded yet.</td></tr>`;
      } else {
        tbodyMarks.innerHTML = stats.recent_marks.map(m => {
          const pct = parseFloat(m.percentage);
          const badgeClass = pct >= 85 ? 'badge-distinction' : (pct >= 70 ? 'badge-first' : (pct >= 40 ? 'badge-second' : 'badge-danger'));
          return `
            <tr>
              <td style="color: var(--text-muted); font-family: var(--font-mono);">${m.marks_id}</td>
              <td style="font-weight: 600; color: #FFF;">${escapeHtml(m.student_name)}</td>
              <td>${escapeHtml(m.subject_name)}</td>
              <td style="text-align: right; font-weight: 600; font-family: var(--font-mono);">${parseFloat(m.marks_obtained).toFixed(1)} / ${m.max_marks}</td>
              <td><span class="badge ${badgeClass}">${pct}%</span></td>
            </tr>
          `;
        }).join('');
      }
    }

  } catch (e) {
    console.error('Error loading dashboard stats:', e);
  }
}

// ==============================================================================
// 4. Student Management Logic
// ==============================================================================

async function loadStudentsData(search = '') {
  const tbody = document.getElementById('tbody-students');
  try {
    const url = search ? `/api/students?search=${encodeURIComponent(search)}` : '/api/students';
    const res = await fetch(url);
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    state.students = json.data;
    if (state.students.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 30px;">No student records found.</td></tr>`;
      return;
    }

    tbody.innerHTML = state.students.map(s => `
      <tr id="student-row-${s.student_id}">
        <td style="text-align: center; font-family: var(--font-mono); color: var(--text-dim);">${s.student_id}</td>
        <td style="font-weight: 600; color: #FFF;">${escapeHtml(s.name)}</td>
        <td style="text-align: center;"><span class="badge" style="background: rgba(255,255,255,0.06);">${escapeHtml(s.roll_no)}</span></td>
        <td style="text-align: center; color: var(--text-muted);">${escapeHtml(s.class_name)}</td>
        <td style="text-align: center; color: var(--text-muted);">${escapeHtml(s.division)}</td>
        <td style="text-align: center;">
          <div class="action-btn-group" style="justify-content: center;">
            <button class="btn-icon" title="Edit Student" onclick="editStudent(${s.student_id})">✏️</button>
            <button class="btn-icon danger" title="Delete Student" onclick="deleteStudent(${s.student_id})">🗑️</button>
          </div>
        </td>
      </tr>
    `).join('');
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--accent-rose); padding: 30px;">Error loading students: ${escapeHtml(e.message)}</td></tr>`;
  }
}

function handleStudentSearch() {
  const val = document.getElementById('search-student-input').value.trim();
  loadStudentsData(val);
}

async function handleStudentSubmit(e) {
  e.preventDefault();
  const feedback = document.getElementById('student-form-msg');
  feedback.className = 'form-feedback';
  feedback.style.display = 'none';

  const payload = {
    name: document.getElementById('student-name-input').value.trim(),
    roll_no: document.getElementById('student-roll-input').value.trim(),
    class_name: document.getElementById('student-class-select').value,
    division: document.getElementById('student-div-select').value,
    student_id: document.getElementById('student-id-input').value.trim() || null
  };

  try {
    const res = await fetch('/api/students', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    showToast(json.message, 'success');
    feedback.innerText = `✓ ${json.message}`;
    feedback.className = 'form-feedback success';
    feedback.style.display = 'block';

    resetStudentForm();
    loadStudentsData();
    loadDropdowns();
  } catch (err) {
    feedback.innerText = `⚠️ ${err.message}`;
    feedback.className = 'form-feedback error';
    feedback.style.display = 'block';
    showToast(err.message, 'error');
  }
}

function editStudent(id) {
  const s = state.students.find(item => item.student_id === id);
  if (!s) return;

  state.editingStudentId = id;
  document.getElementById('student-id-input').value = s.student_id;
  document.getElementById('student-id-input').disabled = true;
  document.getElementById('student-name-input').value = s.name;
  document.getElementById('student-roll-input').value = s.roll_no;
  document.getElementById('student-class-select').value = s.class_name;
  document.getElementById('student-div-select').value = s.division;

  document.getElementById('btn-save-student').style.display = 'none';
  document.getElementById('btn-update-student').style.display = 'block';

  // Highlight table row
  document.querySelectorAll('#tbody-students tr').forEach(r => r.classList.remove('selected'));
  const row = document.getElementById(`student-row-${id}`);
  if (row) row.classList.add('selected');
}

async function handleStudentUpdate() {
  if (!state.editingStudentId) return;
  const feedback = document.getElementById('student-form-msg');

  const payload = {
    name: document.getElementById('student-name-input').value.trim(),
    roll_no: document.getElementById('student-roll-input').value.trim(),
    class_name: document.getElementById('student-class-select').value,
    division: document.getElementById('student-div-select').value
  };

  try {
    const res = await fetch(`/api/students/${state.editingStudentId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    showToast(json.message, 'success');
    resetStudentForm();
    loadStudentsData();
    loadDropdowns();
  } catch (err) {
    feedback.innerText = `⚠️ ${err.message}`;
    feedback.className = 'form-feedback error';
    feedback.style.display = 'block';
    showToast(err.message, 'error');
  }
}

async function deleteStudent(id) {
  if (!confirm(`Are you sure you want to delete Student #${id}?\n\nNote: If marks exist for this student, the foreign key constraint will prevent deletion.`)) {
    return;
  }

  try {
    const res = await fetch(`/api/students/${id}`, { method: 'DELETE' });
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    showToast(json.message, 'success');
    loadStudentsData();
    loadDropdowns();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function resetStudentForm() {
  state.editingStudentId = null;
  document.getElementById('student-form').reset();
  document.getElementById('student-id-input').disabled = false;
  document.getElementById('btn-save-student').style.display = 'block';
  document.getElementById('btn-update-student').style.display = 'none';
  document.querySelectorAll('#tbody-students tr').forEach(r => r.classList.remove('selected'));
  document.getElementById('student-form-msg').style.display = 'none';
}

// ==============================================================================
// 5. Subject Management Logic
// ==============================================================================

async function loadSubjectsData(search = '') {
  const tbody = document.getElementById('tbody-subjects');
  try {
    const url = search ? `/api/subjects?search=${encodeURIComponent(search)}` : '/api/subjects';
    const res = await fetch(url);
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    state.subjects = json.data;
    if (state.subjects.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--text-dim); padding: 30px;">No subjects found.</td></tr>`;
      return;
    }

    tbody.innerHTML = state.subjects.map(s => `
      <tr id="subject-row-${s.subject_id}">
        <td style="text-align: center; font-family: var(--font-mono); color: var(--text-dim);">${s.subject_id}</td>
        <td style="font-weight: 600; color: #FFF;">${escapeHtml(s.subject_name)}</td>
        <td style="text-align: center; font-weight: 600; font-family: var(--font-mono); color: #60A5FA;">${s.max_marks}</td>
        <td style="text-align: center;"><span class="badge" style="background: rgba(255,255,255,0.06);">${s.marks_count || 0} evaluations</span></td>
        <td style="text-align: center;">
          <div class="action-btn-group" style="justify-content: center;">
            <button class="btn-icon" title="Edit Subject" onclick="editSubject(${s.subject_id})">✏️</button>
            <button class="btn-icon danger" title="Delete Subject" onclick="deleteSubject(${s.subject_id})">🗑️</button>
          </div>
        </td>
      </tr>
    `).join('');
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--accent-rose); padding: 30px;">Error loading subjects: ${escapeHtml(e.message)}</td></tr>`;
  }
}

function handleSubjectSearch() {
  const val = document.getElementById('search-subject-input').value.trim();
  loadSubjectsData(val);
}

async function handleSubjectSubmit(e) {
  e.preventDefault();
  const feedback = document.getElementById('subject-form-msg');
  feedback.className = 'form-feedback';
  feedback.style.display = 'none';

  const payload = {
    subject_name: document.getElementById('subject-name-input').value.trim(),
    max_marks: parseInt(document.getElementById('subject-max-input').value),
    subject_id: document.getElementById('subject-id-input').value.trim() || null
  };

  try {
    const res = await fetch('/api/subjects', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    showToast(json.message, 'success');
    feedback.innerText = `✓ ${json.message}`;
    feedback.className = 'form-feedback success';
    feedback.style.display = 'block';

    resetSubjectForm();
    loadSubjectsData();
    loadDropdowns();
  } catch (err) {
    feedback.innerText = `⚠️ ${err.message}`;
    feedback.className = 'form-feedback error';
    feedback.style.display = 'block';
    showToast(err.message, 'error');
  }
}

function editSubject(id) {
  const s = state.subjects.find(item => item.subject_id === id);
  if (!s) return;

  state.editingSubjectId = id;
  document.getElementById('subject-id-input').value = s.subject_id;
  document.getElementById('subject-id-input').disabled = true;
  document.getElementById('subject-name-input').value = s.subject_name;
  document.getElementById('subject-max-input').value = s.max_marks;

  document.getElementById('btn-save-subject').style.display = 'none';
  document.getElementById('btn-update-subject').style.display = 'block';

  document.querySelectorAll('#tbody-subjects tr').forEach(r => r.classList.remove('selected'));
  const row = document.getElementById(`subject-row-${id}`);
  if (row) row.classList.add('selected');
}

async function handleSubjectUpdate() {
  if (!state.editingSubjectId) return;
  const feedback = document.getElementById('subject-form-msg');

  const payload = {
    subject_name: document.getElementById('subject-name-input').value.trim(),
    max_marks: parseInt(document.getElementById('subject-max-input').value)
  };

  try {
    const res = await fetch(`/api/subjects/${state.editingSubjectId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    showToast(json.message, 'success');
    resetSubjectForm();
    loadSubjectsData();
    loadDropdowns();
  } catch (err) {
    feedback.innerText = `⚠️ ${err.message}`;
    feedback.className = 'form-feedback error';
    feedback.style.display = 'block';
    showToast(err.message, 'error');
  }
}

async function deleteSubject(id) {
  if (!confirm(`Are you sure you want to delete Subject #${id}?\n\nNote: If student marks exist for this subject, deletion will be blocked by foreign key integrity.`)) {
    return;
  }

  try {
    const res = await fetch(`/api/subjects/${id}`, { method: 'DELETE' });
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    showToast(json.message, 'success');
    loadSubjectsData();
    loadDropdowns();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function resetSubjectForm() {
  state.editingSubjectId = null;
  document.getElementById('subject-form').reset();
  document.getElementById('subject-id-input').disabled = false;
  document.getElementById('btn-save-subject').style.display = 'block';
  document.getElementById('btn-update-subject').style.display = 'none';
  document.querySelectorAll('#tbody-subjects tr').forEach(r => r.classList.remove('selected'));
  document.getElementById('subject-form-msg').style.display = 'none';
}

// ==============================================================================
// 6. Marks Management Logic
// ==============================================================================

async function loadMarksData() {
  const tbody = document.getElementById('tbody-marks');
  const classFilter = document.getElementById('filter-marks-class') ? document.getElementById('filter-marks-class').value : 'ALL';
  const search = document.getElementById('search-marks-input') ? document.getElementById('search-marks-input').value.trim() : '';

  let url = '/api/marks?';
  if (classFilter && classFilter !== 'ALL') url += `class=${encodeURIComponent(classFilter)}&`;
  if (search) url += `search=${encodeURIComponent(search)}&`;

  try {
    const res = await fetch(url);
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    state.marks = json.data;
    if (state.marks.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--text-dim); padding: 30px;">No marks records matching filter.</td></tr>`;
      return;
    }

    tbody.innerHTML = state.marks.map(m => {
      const pct = parseFloat(m.percentage);
      const badgeClass = pct >= 85 ? 'badge-distinction' : (pct >= 70 ? 'badge-first' : (pct >= 40 ? 'badge-second' : 'badge-danger'));
      return `
        <tr id="marks-row-${m.marks_id}">
          <td style="text-align: center; font-family: var(--font-mono); color: var(--text-dim);">${m.marks_id}</td>
          <td style="text-align: center;"><span class="badge" style="background: rgba(255,255,255,0.06);">${escapeHtml(m.roll_no)}</span></td>
          <td style="font-weight: 600; color: #FFF;">${escapeHtml(m.student_name)}</td>
          <td style="text-align: center; color: var(--text-muted);">${escapeHtml(m.class_name)} - ${escapeHtml(m.division)}</td>
          <td>${escapeHtml(m.subject_name)}</td>
          <td style="text-align: right; font-weight: 700; font-family: var(--font-mono); color: #FFF;">${parseFloat(m.marks_obtained).toFixed(1)}</td>
          <td style="text-align: right; color: var(--text-dim); font-family: var(--font-mono);">${m.max_marks}</td>
          <td><span class="badge ${badgeClass}">${pct}%</span></td>
          <td style="text-align: center;">
            <div class="action-btn-group" style="justify-content: center;">
              <button class="btn-icon" title="Edit Score" onclick="editMarks(${m.marks_id})">✏️</button>
              <button class="btn-icon danger" title="Delete Score" onclick="deleteMarks(${m.marks_id})">🗑️</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="9" style="text-align: center; color: var(--accent-rose); padding: 30px;">Error loading marks: ${escapeHtml(e.message)}</td></tr>`;
  }
}

async function handleMarksSubmit(e) {
  e.preventDefault();
  const feedback = document.getElementById('marks-form-msg');
  feedback.className = 'form-feedback';
  feedback.style.display = 'none';

  const payload = {
    student_id: parseInt(document.getElementById('marks-student-select').value),
    subject_id: parseInt(document.getElementById('marks-subject-select').value),
    marks_obtained: parseFloat(document.getElementById('marks-score-input').value)
  };

  try {
    const res = await fetch('/api/marks', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    showToast(json.message, 'success');
    feedback.innerText = `✓ ${json.message}`;
    feedback.className = 'form-feedback success';
    feedback.style.display = 'block';

    resetMarksForm();
    loadMarksData();
  } catch (err) {
    feedback.innerText = `⚠️ ${err.message}`;
    feedback.className = 'form-feedback error';
    feedback.style.display = 'block';
    showToast(err.message, 'error');
  }
}

function editMarks(id) {
  const m = state.marks.find(item => item.marks_id === id);
  if (!m) return;

  state.editingMarksId = id;
  document.getElementById('marks-student-select').value = m.student_id;
  document.getElementById('marks-student-select').disabled = true;
  document.getElementById('marks-subject-select').value = m.subject_id;
  document.getElementById('marks-subject-select').disabled = true;
  updateMaxMarksHint();

  document.getElementById('marks-score-input').value = m.marks_obtained;

  document.getElementById('btn-save-marks').style.display = 'none';
  document.getElementById('btn-update-marks').style.display = 'block';

  document.querySelectorAll('#tbody-marks tr').forEach(r => r.classList.remove('selected'));
  const row = document.getElementById(`marks-row-${id}`);
  if (row) row.classList.add('selected');
}

async function handleMarksUpdate() {
  if (!state.editingMarksId) return;
  const feedback = document.getElementById('marks-form-msg');

  const payload = {
    marks_obtained: parseFloat(document.getElementById('marks-score-input').value)
  };

  try {
    const res = await fetch(`/api/marks/${state.editingMarksId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    showToast(json.message, 'success');
    resetMarksForm();
    loadMarksData();
  } catch (err) {
    feedback.innerText = `⚠️ ${err.message}`;
    feedback.className = 'form-feedback error';
    feedback.style.display = 'block';
    showToast(err.message, 'error');
  }
}

async function deleteMarks(id) {
  if (!confirm(`Are you sure you want to delete Marks record #${id}?`)) return;

  try {
    const res = await fetch(`/api/marks/${id}`, { method: 'DELETE' });
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    showToast(json.message, 'success');
    loadMarksData();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function resetMarksForm() {
  state.editingMarksId = null;
  document.getElementById('marks-form').reset();
  document.getElementById('marks-student-select').disabled = false;
  document.getElementById('marks-subject-select').disabled = false;
  document.getElementById('marks-subject-hint').innerText = 'Subject maximum: -- marks';
  document.getElementById('btn-save-marks').style.display = 'block';
  document.getElementById('btn-update-marks').style.display = 'none';
  document.querySelectorAll('#tbody-marks tr').forEach(r => r.classList.remove('selected'));
  document.getElementById('marks-form-msg').style.display = 'none';
}

// ==============================================================================
// 7. Results & Marksheet Logic
// ==============================================================================

async function loadStudentMarksheet() {
  const sel = document.getElementById('results-student-select');
  const studentId = sel ? sel.value : null;

  const card = document.getElementById('marksheet-display');
  const empty = document.getElementById('marksheet-empty-state');

  if (!studentId) {
    if (card) card.style.display = 'none';
    if (empty) empty.style.display = 'block';
    return;
  }

  try {
    const res = await fetch(`/api/results/student/${studentId}`);
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    const { student, subject_marks, summary } = json.data;
    if (!student) return;

    if (empty) empty.style.display = 'none';
    if (card) card.style.display = 'block';

    document.getElementById('ms-student-name').innerText = student.name;
    document.getElementById('ms-student-roll').innerText = student.roll_no;
    document.getElementById('ms-student-class-div').innerText = `${student.class_name} - Division ${student.division}`;
    document.getElementById('ms-student-id').innerText = student.student_id;

    // Badging & Percentages
    const pct = parseFloat(summary.overall_percentage || 0);
    const gradeBadge = document.getElementById('marksheet-grade-badge');
    if (pct >= 85) {
      gradeBadge.className = 'badge badge-distinction';
      gradeBadge.innerText = 'FIRST CLASS WITH DISTINCTION';
    } else if (pct >= 70) {
      gradeBadge.className = 'badge badge-first';
      gradeBadge.innerText = 'FIRST CLASS';
    } else if (pct >= 50) {
      gradeBadge.className = 'badge badge-second';
      gradeBadge.innerText = 'SECOND CLASS';
    } else if (pct > 0) {
      gradeBadge.className = 'badge badge-danger';
      gradeBadge.innerText = 'PASS CLASS';
    } else {
      gradeBadge.className = 'badge badge-danger';
      gradeBadge.innerText = 'UNASSESSED';
    }

    document.getElementById('ms-marks-ratio').innerText = `Total Marks: ${summary.total_obtained} / ${summary.total_max}`;
    document.getElementById('ms-overall-pct').innerText = `${pct.toFixed(2)}%`;

    const tbody = document.getElementById('tbody-marksheet-subjects');
    if (subject_marks.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-dim); padding: 30px;">No subject marks recorded for this student yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = subject_marks.map((sub, idx) => {
      const subPct = parseFloat(sub.percentage);
      return `
        <tr>
          <td style="text-align: center; color: var(--text-dim); font-family: var(--font-mono);">${idx + 1}</td>
          <td style="font-weight: 600; color: #FFF;">${escapeHtml(sub.subject_name)}</td>
          <td style="text-align: right; font-family: var(--font-mono); color: var(--text-dim);">${sub.max_marks}</td>
          <td style="text-align: right; font-weight: 700; font-family: var(--font-mono); color: #FFF;">${parseFloat(sub.marks_obtained).toFixed(1)}</td>
          <td>
            <div class="score-progress-wrap">
              <div class="progress-bar-bg">
                <div class="progress-bar-fill ${subPct >= 85 ? 'distinction' : (subPct >= 70 ? 'first' : 'second')}" style="width: ${subPct}%"></div>
              </div>
            </div>
          </td>
          <td style="text-align: center;"><span class="badge ${subPct >= 85 ? 'badge-distinction' : (subPct >= 70 ? 'badge-first' : 'badge-second')}">${subPct}%</span></td>
        </tr>
      `;
    }).join('');

  } catch (err) {
    showToast(`Failed to load marksheet: ${err.message}`, 'error');
  }
}

// ==============================================================================
// 8. SQL Analytical Reports & Console Logic
// ==============================================================================

async function loadPresetQueries() {
  try {
    const res = await fetch('/api/sql/presets');
    const json = await res.json();
    if (json.success) {
      json.presets.forEach(p => {
        state.sqlPresets[p.id] = p.sql;
      });
    }
  } catch (e) {
    console.error('Failed to load SQL presets:', e);
  }
}

function setPresetQuery(id) {
  const query = state.sqlPresets[id];
  if (query) {
    document.getElementById('sql-console-input').value = query;
  }
}

async function executeCustomQuery() {
  const query = document.getElementById('sql-console-input').value.trim();
  if (!query) {
    showToast('Please enter an SQL query first.', 'info');
    return;
  }

  const thead = document.getElementById('thead-report');
  const tbody = document.getElementById('tbody-report');
  const title = document.getElementById('report-title');
  const countLabel = document.getElementById('report-count-label');
  const timing = document.getElementById('sql-query-timing');

  title.innerText = 'Interactive SQL Query Execution';
  tbody.innerHTML = `<tr><td style="text-align: center; color: var(--text-dim); padding: 30px;">Executing query against PostgreSQL...</td></tr>`;

  const startTime = performance.now();
  try {
    const res = await fetch('/api/sql/execute', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query })
    });
    const json = await res.json();
    const duration = (performance.now() - startTime).toFixed(1);
    timing.innerText = `Executed in ${duration} ms`;

    if (!json.success) throw new Error(json.error);

    countLabel.innerText = `${json.count} rows returned`;

    if (json.count === 0) {
      thead.innerHTML = `<tr><th>Query Result</th></tr>`;
      tbody.innerHTML = `<tr><td style="text-align: center; color: var(--text-dim); padding: 30px;">Query succeeded with 0 matching rows.</td></tr>`;
      return;
    }

    // Render Table Headers
    thead.innerHTML = `<tr>${json.columns.map(c => `<th>${escapeHtml(c)}</th>`).join('')}</tr>`;

    // Render Table Rows
    tbody.innerHTML = json.rows.map(row => `
      <tr>${json.columns.map(c => `<td>${escapeHtml(String(row[c] !== null && row[c] !== undefined ? row[c] : 'NULL'))}</td>`).join('')}</tr>
    `).join('');

    showToast(`Query executed: ${json.count} rows`, 'success');

  } catch (err) {
    timing.innerText = '';
    countLabel.innerText = 'Error';
    thead.innerHTML = `<tr><th>SQL Error</th></tr>`;
    tbody.innerHTML = `<tr><td style="color: var(--accent-rose); padding: 25px;">${escapeHtml(err.message)}</td></tr>`;
    showToast(err.message, 'error');
  }
}

async function loadReport(type) {
  const thead = document.getElementById('thead-report');
  const tbody = document.getElementById('tbody-report');
  const title = document.getElementById('report-title');
  const countLabel = document.getElementById('report-count-label');

  const titles = {
    'student-wise': 'Report 1: Student-wise Marks (Multi-table INNER JOIN)',
    'subject-performance': 'Report 2: Subject Performance Metrics (COUNT, AVG, MIN, MAX)',
    'class-summary': 'Report 3: Class & Division Summary (GROUP BY Class, Div)',
    'without-marks': 'Report 4: Students Without Any Marks Recorded (LEFT JOIN with IS NULL)'
  };
  title.innerText = titles[type] || 'Analytical Report';
  tbody.innerHTML = `<tr><td style="text-align: center; color: var(--text-dim); padding: 30px;">Loading analytical report from PostgreSQL...</td></tr>`;

  try {
    const res = await fetch(`/api/reports/${type}`);
    const json = await res.json();
    if (!json.success) throw new Error(json.error);

    const rows = json.data;
    countLabel.innerText = `${rows.length} rows returned`;

    if (rows.length === 0) {
      thead.innerHTML = `<tr><th>Report Result</th></tr>`;
      tbody.innerHTML = `<tr><td style="text-align: center; color: var(--text-dim); padding: 30px;">No data matching report criteria.</td></tr>`;
      return;
    }

    const columns = Object.keys(rows[0]);
    thead.innerHTML = `<tr>${columns.map(c => `<th>${escapeHtml(c.replace(/_/g, ' ').toUpperCase())}</th>`).join('')}</tr>`;
    tbody.innerHTML = rows.map(r => `
      <tr>${columns.map(c => `<td>${escapeHtml(String(r[c] !== null && r[c] !== undefined ? r[c] : '-'))}</td>`).join('')}</tr>
    `).join('');

    showToast(`Loaded ${rows.length} report rows`, 'success');
  } catch (err) {
    countLabel.innerText = 'Error';
    thead.innerHTML = `<tr><th>Error</th></tr>`;
    tbody.innerHTML = `<tr><td style="color: var(--accent-rose); padding: 25px;">${escapeHtml(err.message)}</td></tr>`;
    showToast(err.message, 'error');
  }
}

// ==============================================================================
// 9. Toast Notification System & Utilities
// ==============================================================================

function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icon = type === 'success' ? '✓' : (type === 'error' ? '✕' : 'ℹ');
  toast.innerHTML = `<span style="font-size: 15px; font-weight: 700;">${icon}</span> <span>${escapeHtml(msg)}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 200ms ease';
    setTimeout(() => toast.remove(), 200);
  }, 4000);
}

function escapeHtml(str) {
  if (typeof str !== 'string') return String(str);
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
