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

  /**
   * Escape dữ liệu trước khi ghép vào chuỗi HTML.
   * MỌI giá trị lấy từ kho dữ liệu (tên dự án, mô tả, tên người dùng...) phải đi qua
   * hàm này trước khi vào innerHTML — nếu ghép thẳng, một hồ sơ đặt tên kiểu
   * <img src=x onerror=...> sẽ chạy được mã trên máy người xem.
   */
  function esc(value) {
    if (value === null || value === undefined) return '';
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
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
    const defs = [
      {
        name: 'Phòng học miễn phí cho trẻ em xóm trọ',
        category: 'Giáo dục',
        icon: ICONS[2],
        cover: COVERS[0],
        location: 'Phường Bình Hưng Hoà, Q. Bình Tân',
        distanceKm: 1.2,
        target: 30000000,
        raised: 21000000,
        lat: BASE_LAT + 0.012, lng: BASE_LNG - 0.02,
        description: 'Cải tạo một phòng sinh hoạt cộng đồng thành lớp học miễn phí buổi tối cho khoảng 25 em nhỏ có hoàn cảnh khó khăn trong xóm trọ, do các bạn sinh viên tình nguyện đứng lớp.',
        creatorName: 'Nguyễn Thị Mai',
        creatorVerified: true,
        milestones: [
          { name: 'Sửa chữa phòng học, lắp bàn ghế', amount: 12000000, status: 'released', desc: 'Đã giải ngân để sửa nền, sơn tường và mua 15 bộ bàn ghế.' },
          { name: 'Mua sách vở, dụng cụ học tập', amount: 8000000, status: 'released', desc: 'Đã giải ngân một phần để mua sách giáo khoa và văn phòng phẩm cho học kỳ đầu.' },
          { name: 'Duy trì chi phí điện nước 6 tháng', amount: 10000000, status: 'locked', desc: 'Sẽ giải ngân khi phòng học chính thức hoạt động và có xác nhận từ đại diện tổ dân phố.' },
        ],
      },
      {
        name: 'Trạm tái chế nhựa khu phố 4',
        category: 'Môi trường',
        icon: ICONS[1],
        cover: COVERS[1],
        location: 'Phường Tân Định, Q.1',
        distanceKm: 2.8,
        target: 45000000,
        raised: 45000000,
        lat: BASE_LAT - 0.008, lng: BASE_LNG + 0.01,
        description: 'Lắp đặt trạm thu gom và phân loại rác nhựa tự động, kết nối với đơn vị tái chế để giảm rác thải nhựa ra kênh rạch trong khu vực.',
        creatorName: 'Trần Văn Khoa',
        creatorVerified: true,
        milestones: [
          { name: 'Mua thùng phân loại và máy ép nhựa mini', amount: 25000000, status: 'released', desc: 'Đã giải ngân để mua 10 thùng phân loại và 1 máy ép nhựa mini.' },
          { name: 'Lắp mái che và biển hướng dẫn', amount: 10000000, status: 'released', desc: 'Đã hoàn thành lắp đặt mái che chống mưa nắng cho trạm.' },
          { name: 'Vận hành thử 3 tháng', amount: 10000000, status: 'released', desc: 'Đã giải ngân toàn bộ, trạm đang vận hành ổn định.' },
        ],
      },
      {
        name: 'Thư viện khu phố mini',
        category: 'Cộng đồng',
        icon: ICONS[0],
        cover: COVERS[4],
        location: 'Phường Linh Đông, TP. Thủ Đức',
        distanceKm: 4.5,
        target: 20000000,
        raised: 6200000,
        lat: BASE_LAT + 0.03, lng: BASE_LNG + 0.025,
        description: 'Xây dựng một tủ sách cộng đồng đặt tại nhà văn hoá khu phố, phục vụ đọc miễn phí cho cư dân mọi lứa tuổi, ưu tiên sách thiếu nhi và kỹ năng sống.',
        creatorName: 'Lê Hoàng Bích',
        creatorVerified: false,
        milestones: [
          { name: 'Đóng kệ sách và bàn đọc', amount: 8000000, status: 'pending', desc: 'Chờ đủ 40% vốn mục tiêu để bắt đầu đặt đóng kệ sách.' },
          { name: 'Mua sách và trang trí không gian', amount: 7000000, status: 'locked', desc: 'Sẽ giải ngân sau khi hoàn thành mốc đóng kệ sách.' },
          { name: 'Tổ chức buổi ra mắt thư viện', amount: 5000000, status: 'locked', desc: 'Sẽ giải ngân khi thư viện sẵn sàng đón độc giả.' },
        ],
      },
      {
        name: 'Cải tạo sân chơi trẻ em công viên nhỏ',
        category: 'Cộng đồng',
        icon: ICONS[3],
        cover: COVERS[3],
        location: 'Phường An Lạc, Q. Bình Tân',
        distanceKm: 3.3,
        target: 35000000,
        raised: 9000000,
        lat: BASE_LAT - 0.02, lng: BASE_LNG - 0.015,
        description: 'Sửa chữa và bổ sung thiết bị chơi an toàn cho khu công viên nhỏ đang xuống cấp, nơi vui chơi duy nhất của trẻ em trong khu phố.',
        creatorName: 'Phạm Quốc Huy',
        creatorVerified: true,
        fraudFlag: { score: 62, reason: '62% ảnh trùng khớp với dự án khác trên mạng' },
        milestones: [
          { name: 'Tháo dỡ thiết bị cũ hư hỏng', amount: 10000000, status: 'pending', desc: 'Chờ giải ngân sau khi có xác nhận khảo sát hiện trạng.' },
          { name: 'Lắp đặt thiết bị chơi mới', amount: 20000000, status: 'locked', desc: 'Sẽ giải ngân sau khi hoàn thành tháo dỡ.' },
          { name: 'Trồng cây xanh, lắp đèn chiếu sáng', amount: 5000000, status: 'locked', desc: 'Sẽ giải ngân ở giai đoạn hoàn thiện cuối cùng.' },
        ],
      },
      {
        name: 'Máy lọc nước sạch cho xóm ven kênh',
        category: 'Sức khoẻ',
        icon: ICONS[4],
        cover: COVERS[2],
        location: 'Phường 6, Q.8',
        distanceKm: 4.9,
        target: 28000000,
        raised: 21000000,
        lat: BASE_LAT + 0.045, lng: BASE_LNG - 0.03,
        description: 'Lắp đặt hệ thống lọc nước sạch dùng chung cho khoảng 40 hộ dân sống ven kênh chưa có nước máy ổn định.',
        creatorName: 'Đỗ Thị Ngọc',
        creatorVerified: true,
        milestones: [
          { name: 'Mua hệ thống lọc và bồn chứa', amount: 18000000, status: 'released', desc: 'Đã giải ngân, thiết bị đang được vận chuyển về khu vực lắp đặt.' },
          { name: 'Thi công đường ống dẫn nước', amount: 10000000, status: 'pending', desc: 'Chờ giải ngân sau khi có báo giá thi công chính thức.' },
        ],
      },
      {
        name: 'Tủ thuốc sơ cứu cộng đồng',
        category: 'Sức khoẻ',
        icon: ICONS[5],
        cover: COVERS[5],
        location: 'Phường Hiệp Bình Chánh, TP. Thủ Đức',
        distanceKm: 4.1,
        target: 15000000,
        raised: 2500000,
        lat: BASE_LAT + 0.06, lng: BASE_LNG + 0.04,
        description: 'Trang bị tủ thuốc và dụng cụ sơ cứu cơ bản đặt tại các điểm sinh hoạt chung, kèm buổi tập huấn sơ cứu miễn phí cho cư dân.',
        creatorName: 'Vũ Minh Tâm',
        creatorVerified: false,
        milestones: [
          { name: 'Mua tủ thuốc và vật tư y tế', amount: 9000000, status: 'pending', desc: 'Chờ giải ngân khi đạt 30% vốn mục tiêu.' },
          { name: 'Tổ chức tập huấn sơ cứu', amount: 6000000, status: 'locked', desc: 'Sẽ giải ngân sau buổi tập huấn đầu tiên.' },
        ],
      },
    ];

    return defs.map((d) => ({
      id: uid('proj'),
      status: 'active',
      createdAt: new Date(Date.now() - Math.random() * 20 * 86400000).toISOString(),
      ...d,
    }));
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
      const projects = seedProjects();
      localStorage.setItem(KEYS.projects, JSON.stringify(projects));
      localStorage.setItem(KEYS.ledger, JSON.stringify(seedLedger(projects)));
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
    try { return JSON.parse(localStorage.getItem(KEYS.user)); } catch (e) { return null; }
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
    return u && (u.role === 'admin' || u.email === 'admin@gmail.com');
  }

  // Gán window.location KHÔNG dừng script đang chạy — trình duyệt thực thi nốt phần còn
  // lại của trang rồi mới điều hướng. Cả hai hàm dưới đây NÉM LỖI để dừng hẳn, tránh
  // trường hợp người chưa đủ quyền vẫn kịp thấy/thao tác nội dung trong lúc chờ chuyển trang.
  function requireLogin() {
    if (!getUser()) {
      window.location.replace('login_page.html');
      throw new Error('LocalVest: chưa đăng nhập — đã dừng render trang.');
    }
  }

  function requireAdmin() {
    const u = getUser();
    if (!u) {
      window.location.replace('login_page.html');
      throw new Error('LocalVest: chưa đăng nhập — đã dừng render trang quản trị.');
    }
    if (!isAdmin()) {
      toast('Bị từ chối: Quyền Quản trị viên mới được phép!', 'error');
      setTimeout(() => { window.location.replace('home.html'); }, 1500);
      throw new Error('LocalVest: tài khoản không có quyền quản trị — đã dừng render trang quản trị.');
    }
  }

  function getProjects() { return JSON.parse(localStorage.getItem(KEYS.projects) || '[]'); }
  function saveProjects(list) { localStorage.setItem(KEYS.projects, JSON.stringify(list)); }
  function getProject(id) { return getProjects().find((p) => p.id === id); }

  function getQueue() { return JSON.parse(localStorage.getItem(KEYS.queue) || '[]'); }
  function saveQueue(list) { localStorage.setItem(KEYS.queue, JSON.stringify(list)); }

  function getLedger(projectId) {
    const all = JSON.parse(localStorage.getItem(KEYS.ledger) || '{}');
    return all[projectId] || [];
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
              <div class="nav-bell-wrap" style="position:relative;">
                <button id="nav-bell-btn" aria-label="Thông báo" style="position:relative;background:none;border:none;cursor:pointer;font-size:20px;padding:6px;">
                  🔔<span id="nav-bell-badge" class="hidden" style="position:absolute;top:0;right:0;background:var(--color-danger,#e55757);color:#fff;font-size:10px;font-weight:700;border-radius:999px;min-width:16px;height:16px;line-height:16px;text-align:center;padding:0 3px;"></span>
                </button>
                <div id="nav-bell-panel" class="hidden" style="position:absolute;right:0;top:36px;width:320px;max-height:380px;overflow-y:auto;background:#fff;border:1px solid var(--color-border,#e2e8f0);border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.15);z-index:200;">
                  <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 14px;border-bottom:1px solid var(--color-border,#e2e8f0);">
                    <strong style="font-size:13px;">Thông báo</strong>
                    <button id="nav-bell-mark-all" style="background:none;border:none;color:var(--color-primary,#2f5496);font-size:12px;cursor:pointer;">Đánh dấu đã đọc hết</button>
                  </div>
                  <div id="nav-bell-list" style="font-size:13px;"><div style="padding:16px;color:#8a9bb5;text-align:center;">Đang tải...</div></div>
                </div>
              </div>
              <div class="nav-avatar">${esc(initials(user.name))}</div>
              <div>
                <div class="nav-user-name">${esc(user.name)}</div>
                <a class="nav-logout" id="nav-logout-btn" href="#">Đăng xuất</a>
              </div>
            ` : `<a class="btn btn-outline btn-sm" href="login_page.html">Đăng nhập</a>`}
          </div>
        </div>
      </nav>
    `;
    const logoutBtn = document.getElementById('nav-logout-btn');
    if (logoutBtn) logoutBtn.addEventListener('click', (e) => { e.preventDefault(); logout(); });
    if (user) wireNotificationBell();
  }

  /**
   * Chuông thông báo — khác LV.toast() (hiện vài giây rồi biến mất), đây là thông báo
   * LƯU TRỮ được: tải qua GET /api/notifications, cập nhật tức thời qua cùng WebSocket
   * /ws/live-feed dùng cho dashboard (sự kiện NOTIFICATION). Chưa có luồng đăng nhập JWT
   * thật (task của Linh) nên tạm tự lấy token bằng tài khoản demo đã seed sẵn trên backend.
   */
  function wireNotificationBell() {
    const NOTI_API = 'http://127.0.0.1:8000';
    const btn = document.getElementById('nav-bell-btn');
    const panel = document.getElementById('nav-bell-panel');
    const badge = document.getElementById('nav-bell-badge');
    const list = document.getElementById('nav-bell-list');
    if (!btn) return;

    let token = null;
    async function getToken() {
      if (token) return token;
      const email = isAdmin() ? 'admin@localvest.vn' : 'demo@localvest.vn';
      const res = await fetch(`${NOTI_API}/api/auth/login`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password: 'x' }),
      });
      if (!res.ok) throw new Error('no backend');
      token = (await res.json()).token;
      return token;
    }

    function renderList(items) {
      list.innerHTML = items.length ? items.map((n) => `
        <div class="nb-item" data-id="${esc(n.id)}" style="padding:10px 14px;border-bottom:1px solid #f1f5f9;cursor:pointer;${n.is_read ? 'opacity:.55;' : 'background:#f8fafc;'}">
          <div style="font-weight:600;">${esc(n.title)}</div>
          <div style="color:#64748b;margin-top:2px;">${esc(n.message)}</div>
          <div style="color:#94a3b8;font-size:11px;margin-top:4px;">${esc(formatDate(n.created_at))}</div>
        </div>`).join('')
        : `<div style="padding:16px;color:#8a9bb5;text-align:center;">Chưa có thông báo nào.</div>`;
      list.querySelectorAll('.nb-item').forEach((el) => el.addEventListener('click', async () => {
        try {
          const t = await getToken();
          await fetch(`${NOTI_API}/api/notifications/${el.dataset.id}/read`, { method: 'POST', headers: { Authorization: `Bearer ${t}` } });
          load();
        } catch (e) { /* backend chưa chạy, bỏ qua */ }
      }));
    }

    async function load() {
      try {
        const t = await getToken();
        const res = await fetch(`${NOTI_API}/api/notifications`, { headers: { Authorization: `Bearer ${t}` } });
        const data = await res.json();
        renderList(data.notifications);
        badge.textContent = data.unreadCount > 9 ? '9+' : String(data.unreadCount);
        badge.classList.toggle('hidden', data.unreadCount === 0);
      } catch (e) {
        list.innerHTML = `<div style="padding:16px;color:#e55757;text-align:center;">⚠ Không kết nối được backend thật.</div>`;
      }
    }

    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      panel.classList.toggle('hidden');
      if (!panel.classList.contains('hidden')) load();
    });
    document.addEventListener('click', (e) => {
      if (!panel.contains(e.target) && e.target !== btn) panel.classList.add('hidden');
    });
    document.getElementById('nav-bell-mark-all').addEventListener('click', async (e) => {
      e.stopPropagation();
      try {
        const t = await getToken();
        await fetch(`${NOTI_API}/api/notifications/read-all`, { method: 'POST', headers: { Authorization: `Bearer ${t}` } });
        load();
      } catch (err) { /* bỏ qua */ }
    });

    // Cập nhật số chưa đọc ngay khi có sự kiện mới, không cần bấm chuông mới thấy
    try {
      const ws = new WebSocket('ws://127.0.0.1:8000/ws/live-feed');
      ws.onmessage = (msg) => {
        const payload = JSON.parse(msg.data);
        if (payload.event === 'NOTIFICATION') load();
      };
      window.addEventListener('beforeunload', () => ws.close());
    } catch (e) { /* backend chưa chạy */ }

    load();
  }

  return {
    KEYS, formatVND, formatDate, haversineKm, ensureSeed, randomName, initials,
    getUser, setUser, logout, requireLogin, requireAdmin, isAdmin,
    getProjects, saveProjects, getProject,
    getQueue, saveQueue,
    getLedger, pushLedger,
    getRegisteredEmails, addRegisteredEmail, checkEmailExists,
    toast, renderNavbar, uid, esc,
    BASE_LAT, BASE_LNG,
  };
})();

LV.ensureSeed();
