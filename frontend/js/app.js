/* ==========================================================================
   LocalVest — Mock backend dùng chung cho frontend MVP (Week 1)
   Không gọi API thật: dữ liệu được seed + lưu trong localStorage để mô phỏng
   Clerk (auth), Supabase (project/escrow), Kafka -> Medallion (ledger real-time).
   ========================================================================== */
const LV = (function () {
  const KEYS = {
    user: 'lv_user',
    projects: 'lv_projects',
    queue: 'lv_queue',
    ledger: 'lv_ledger',
    registeredEmails: 'lv_registered_emails',
  };

  const COVERS = ['cover-a', 'cover-b', 'cover-c', 'cover-d', 'cover-e', 'cover-f'];
  const ICONS = ['📚', '♻️', '🎓', '🌳', '🚰', '🏥'];

  // Toạ độ gốc mô phỏng (trung tâm Q.1, TP.HCM) — dùng để tính khoảng cách khi có GPS thật
  const BASE_LAT = 10.7769;
  const BASE_LNG = 106.7009;

  function uid(prefix) {
    return prefix + '_' + Math.random().toString(36).slice(2, 9);
  }

  function formatVND(n) {
    return Math.round(n).toLocaleString('vi-VN') + 'đ';
  }

  function formatDate(iso) {
    const d = new Date(iso);
    return d.toLocaleDateString('vi-VN') + ' ' + d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
  }

  function haversineKm(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) ** 2 +
      Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  function seedProjects() {
    // Removed - Backend is now the SSOT for projects
    return [];
  }

  function seedLedger(projects) {
    const ledger = {};
    projects.forEach((p) => {
      const entries = [];
      // Chia đều p.raised thành nhiều khoản đóng góp ngẫu nhiên, tổng khớp chính xác
      // với số tiền đã gọi vốn của dự án để số dư escrow (raised - released) không bị âm/lệch.
      const steps = 4 + Math.floor(Math.random() * 3);
      const weights = Array.from({ length: steps }, () => 0.4 + Math.random());
      const weightSum = weights.reduce((s, w) => s + w, 0);
      let allocated = 0;
      for (let i = 0; i < steps; i++) {
        const amt = i === steps - 1
          ? p.raised - allocated
          : Math.max(10000, Math.round((p.raised * weights[i] / weightSum) / 10000) * 10000);
        allocated += amt;
        entries.push({
          time: new Date(Date.now() - (steps - i) * 3600 * 1000).toISOString(),
          amount: amt,
          type: 'in',
          desc: `+${formatVND(amt)} từ ${randomName()}`,
        });
      }
      p.milestones.filter((m) => m.status === 'released').forEach((m) => {
        entries.push({
          time: new Date(Date.now() - Math.random() * 3600 * 1000).toISOString(),
          amount: m.amount,
          type: 'out',
          desc: `Giải ngân mốc "${m.name}"`,
        });
      });
      entries.sort((a, b) => new Date(a.time) - new Date(b.time));
      ledger[p.id] = entries;
    });
    return ledger;
  }

  const FIRST = ['Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Vũ', 'Đặng', 'Bùi', 'Đỗ', 'Ngô'];
  const LAST = ['Văn An', 'Thị Bình', 'Minh Khôi', 'Thu Hà', 'Quốc Bảo', 'Ngọc Linh', 'Hữu Phát', 'Thanh Tùng'];
  function randomName() {
    return FIRST[Math.floor(Math.random() * FIRST.length)] + ' ' + LAST[Math.floor(Math.random() * LAST.length)];
  }

  // Seed admin account
  function ensureAdminAccount() {
    const emails = getRegisteredEmails();
    if (!emails.includes('admin@gmail.com')) {
      emails.push('admin@gmail.com');
      localStorage.setItem(KEYS.registeredEmails, JSON.stringify(emails));
    }
    // Ensure admin user object in a known key for role lookup
    if (!localStorage.getItem('lv_admin_seeded')) {
      localStorage.setItem('lv_admin_seeded', '1');
    }
  }

  function ensureSeed() {
    ensureAdminAccount();
    if (!localStorage.getItem(KEYS.projects)) {
      // Dummy check to prevent re-seeding ledger unnecessarily
      localStorage.setItem(KEYS.projects, '[]');
      localStorage.setItem(KEYS.ledger, JSON.stringify({}));
    }
    if (!localStorage.getItem(KEYS.queue)) {
      localStorage.setItem(KEYS.queue, JSON.stringify([
        {
          id: uid('sub'),
          projectName: 'Bếp ăn 0 đồng cuối tuần',
          creatorName: 'Trịnh Gia Bảo',
          submittedAt: new Date(Date.now() - 2 * 3600 * 1000).toISOString(),
          status: 'pending',
          fraudScore: 80,
          fraudReason: '80% trùng ảnh với dự án đã đăng trên nền tảng khác',
          target: 25000000,
          description: 'Tổ chức nấu và phát cơm miễn phí vào cuối tuần cho người lao động khó khăn quanh khu vực.',
          location: 'Phường Tân Thới Hiệp, Q.12',
          milestones: [
            { name: 'Mua nguyên liệu và dụng cụ nấu ăn', amount: 15000000 },
            { name: 'Chi phí vận hành 2 tháng', amount: 10000000 },
          ],
        },
        {
          id: uid('sub'),
          projectName: 'Góc học tập ngoài trời cho xóm ven sông',
          creatorName: 'Lâm Thuý Vy',
          submittedAt: new Date(Date.now() - 26 * 3600 * 1000).toISOString(),
          status: 'pending',
          fraudScore: 12,
          fraudReason: 'Không phát hiện dấu hiệu bất thường',
          target: 18000000,
          description: 'Dựng một khu vực học tập có mái che ngoài trời cho trẻ em xóm ven sông chưa có điều kiện học tại nhà.',
          location: 'Phường Thạnh Lộc, Q.12',
          milestones: [
            { name: 'Dựng khung mái che', amount: 10000000 },
            { name: 'Mua bàn ghế và đèn học', amount: 8000000 },
          ],
        },
      ]));
    }
    if (!localStorage.getItem(KEYS.registeredEmails)) {
      localStorage.setItem(KEYS.registeredEmails, JSON.stringify(['demo@localvest.vn']));
    }
  }

  function getUser() {
    try { 
      const u = JSON.parse(localStorage.getItem(KEYS.user)); 
      if (u) u.token = localStorage.getItem('lv_token') || u.token;
      return u;
    } catch (e) { return null; }
  }
  function getRegisteredEmails() {
    return JSON.parse(localStorage.getItem(KEYS.registeredEmails) || '[]');
  }
  function addRegisteredEmail(email) {
    const list = getRegisteredEmails();
    const lower = email.toLowerCase();
    if (!list.includes(lower)) { list.push(lower); localStorage.setItem(KEYS.registeredEmails, JSON.stringify(list)); }
  }
  async function checkEmailExists(email) {
    await new Promise((r) => setTimeout(r, 500));
    return getRegisteredEmails().includes(email.toLowerCase());
  }
  function setUser(u) { localStorage.setItem(KEYS.user, JSON.stringify(u)); }
  function logout() { localStorage.removeItem(KEYS.user); window.location.href = 'login_page.html'; }

  function isAdmin() {
    const u = getUser();
    return u && u.role === 'admin';
  }

  function requireLogin() {
    if (!getUser()) window.location.href = 'login_page.html';
  }

  function requireAdmin() {
    const u = getUser();
    if (!u) { window.location.href = 'login_page.html'; return; }
    if (!isAdmin()) {
      toast('Bị từ chối: Quyền Quản trị viên mới được phép!', 'error');
      setTimeout(() => { window.location.href = 'home.html'; }, 1500);
    }
  }

  // Async API calls to Backend
  async function getCampaigns() {
    try {
      const u = getUser();
      const headers = {};
      if (u && u.token) {
        headers['Authorization'] = `Bearer ${u.token}`;
      }
      const res = await fetch('/api/campaigns', { headers });
      const data = await res.json();
      return data.projects || [];
    } catch (err) {
      console.error(err);
      return [];
    }
  }

  async function getNearbyCampaigns(lat = BASE_LAT, lng = BASE_LNG, radius = 5.0) {
    try {
      const res = await fetch(`/api/location/nearby?lat=${lat}&lng=${lng}&radius_km=${radius}`);
      const data = await res.json();
      return data; // Return full object so frontend knows final radius
    } catch (err) {
      console.error(err);
      return { projects: [], radius_km: radius };
    }
  }

  async function getCampaignDetail(id) {
    try {
      const res = await fetch(`/api/campaigns/${id}`);
      if (!res.ok) return null;
      const data = await res.json();
      return data.project;
    } catch (err) {
      console.error(err);
      return null;
    }
  }

  // Deprecated synchronous functions (kept as empty to avoid crash if some old code calls them before being updated)
  function getProjects() { return []; }
  function saveProjects(list) { }
  function getProject(id) { return null; }

  function getQueue() { return JSON.parse(localStorage.getItem(KEYS.queue) || '[]'); }
  function saveQueue(list) { localStorage.setItem(KEYS.queue, JSON.stringify(list)); }

  async function getLedger(projectId) {
    try {
      const res = await fetch(`/api/campaigns/${projectId}/ledger`);
      if (!res.ok) return [];
      const data = await res.json();
      return data.ledger || [];
    } catch (err) {
      console.error(err);
      return [];
    }
  }
  function pushLedger(projectId, entry) {
    const all = JSON.parse(localStorage.getItem(KEYS.ledger) || '{}');
    all[projectId] = all[projectId] || [];
    all[projectId].push(entry);
    localStorage.setItem(KEYS.ledger, JSON.stringify(all));
  }

  function toast(message, type) {
    let root = document.getElementById('toast-root');
    if (!root) {
      root = document.createElement('div');
      root.id = 'toast-root';
      document.body.appendChild(root);
    }
    const el = document.createElement('div');
    el.className = 'toast' + (type ? ' toast-' + type : '');
    el.textContent = message;
    root.appendChild(el);
    setTimeout(() => el.remove(), 3200);
  }

  function initials(name) {
    return (name || '?').trim().split(/\s+/).slice(-2).map((w) => w[0]).join('').toUpperCase();
  }

  function renderNavbar(active) {
    const root = document.getElementById('navbar-root');
    if (!root) return;
    const user = getUser();
    root.innerHTML = `
      <nav class="navbar">
        <div class="navbar-inner">
          <a class="brand" href="home.html">
            <div class="auth-logo-badge">
              <img src="https://gmcconsultingvn.com/wp-content/uploads/2022/03/ic-ft-2.png" alt="Handshake Logo" class="logo-icon">
            </div> LocalVest
          </a>
          <div class="nav-links">
            <a class="nav-link ${active === 'home' ? 'active' : ''}" href="home.html">Khám phá</a>
            <a class="nav-link ${active === 'dashboard' ? 'active' : ''}" href="dashboard.html">Dòng tiền</a>
            <a class="nav-link ${active === 'submit' ? 'active' : ''}" href="submit_project.html">Đăng dự án</a>
            ${isAdmin() ? `<a class="nav-link ${active === 'admin' ? 'active' : ''}" href="admin.html" style="color:#d4a843;font-weight:700;">🛡️ Quản trị</a>` : ''}
          </div>
          <div class="nav-user">
            ${user ? `
              <div class="nav-avatar">${initials(user.name)}</div>
              <div>
                <div class="nav-user-name">${user.name}</div>
                <a class="nav-logout" id="nav-logout-btn" href="#">Đăng xuất</a>
              </div>
            ` : `<a class="btn btn-outline btn-sm" href="login_page.html">Đăng nhập</a>`}
          </div>
        </div>
      </nav>
    `;
    const logoutBtn = document.getElementById('nav-logout-btn');
    if (logoutBtn) logoutBtn.addEventListener('click', (e) => { e.preventDefault(); logout(); });
  }

  function initLiveFeed() {
    const wsUrl = 'ws://' + (window.location.hostname || '127.0.0.1') + ':8000/ws/live-feed';
    let ws = new WebSocket(wsUrl);
    
    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.event === 'NEW_TRANSACTION') {
          const data = payload.data;
          // Because projects are now fetched from the backend, we don't strictly need to update localStorage here.
          // The backend maintains the SSOT. But we can update if a project is locally cached, though it's not needed anymore.
          
          const entry = {
            time: payload.timestamp,
            amount: data.amount,
            type: 'in',
            desc: `+${formatVND(data.amount)} từ ${data.backerName}`
          };
          pushLedger(data.projectId, entry);
          
          // Dispatch custom event for UI to update realtime
          window.dispatchEvent(new CustomEvent('LiveFeedUpdate', { detail: data }));
          toast(`Mới: +${formatVND(data.amount)} từ ${data.backerName}`, 'success');
        }
      } catch (err) {
        console.error('Error parsing live feed:', err);
      }
    };

    ws.onclose = () => {
      setTimeout(initLiveFeed, 3000); // Reconnect
    };
  }

  return {
    KEYS, formatVND, formatDate, haversineKm, ensureSeed, randomName, initials,
    getUser, setUser, logout, requireLogin, requireAdmin, isAdmin,
    getCampaigns, getNearbyCampaigns, getCampaignDetail,
    getProjects, saveProjects, getProject, // Deprecated
    getQueue, saveQueue,
    getLedger, pushLedger,
    getRegisteredEmails, addRegisteredEmail, checkEmailExists,
    toast, renderNavbar, uid, initLiveFeed,
    BASE_LAT, BASE_LNG,
  };
})();

LV.ensureSeed();
LV.initLiveFeed();
