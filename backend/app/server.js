/* ==========================================================================
   LocalVest Backend Server — Node.js Express + Socket.io (Realtime Live Feed)
   Architected for 8 Core Services (Round 2 Requirements)
   Zero Cost Stack: Ready to deploy on Render / Koyeb / Vercel Serverless
   ========================================================================== */

const express = require('express');
const http = require('http');
const cors = require('cors');
const { Server } = require('socket.io');
const jwt = require('jsonwebtoken');
const { pool, memoryStore, haversineKm } = require('./services/store');

const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: '*', methods: ['GET', 'POST'] }
});

const JWT_SECRET = process.env.JWT_SECRET || 'localvest_super_secret_jwt_key_2026';
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());

// Socket.io Realtime Live Feed Connection
io.on('connection', (socket) => {
  console.log('⚡ [Realtime Live Feed] Client connected:', socket.id);
  socket.on('disconnect', () => console.log('Client disconnected:', socket.id));
});

// Helper Function: Emit Realtime Live Feed Event
function broadcastLiveFeed(event, data) {
  io.emit(event, {
    timestamp: new Date().toISOString(),
    ...data
  });
}

// Middleware: Authentication & RBAC (Role-Based Access Control)
function authenticate(req, res, next) {
  const authHeader = req.headers.authorization;
  if (!authHeader) return res.status(401).json({ error: 'Chưa cung cấp token xác thực' });
  const token = authHeader.split(' ')[1];
  try {
    const decoded = jwt.verify(token, JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(403).json({ error: 'Token không hợp lệ hoặc đã hết hạn' });
  }
}

function requireRole(role) {
  return (req, res, next) => {
    if (req.user && req.user.role === role) return next();
    return res.status(403).json({ error: `Quyền truy cập bị từ chối. Yêu cầu vai trò ${role}` });
  };
}

// ==========================================================================
// 1. AUTH & USER SERVICE
// ==========================================================================
app.post('/api/auth/register', (req, res) => {
  const { email, password, full_name, role } = req.body;
  if (!email || !password || !full_name) {
    return res.status(400).json({ error: 'Vui lòng cung cấp đầy đủ thông tin' });
  }
  const existing = memoryStore.users.find(u => u.email.toLowerCase() === email.toLowerCase());
  if (existing) return res.status(400).json({ error: 'Email đã được đăng ký' });

  const newUser = {
    id: 'usr_' + Math.random().toString(36).substring(2, 9),
    email,
    full_name,
    role: role || 'backer', // backer, project_owner, admin
    kyc_status: 'pending',
    is_locked: false,
    created_at: new Date().toISOString()
  };
  memoryStore.users.push(newUser);

  const token = jwt.sign({ id: newUser.id, email: newUser.email, role: newUser.role }, JWT_SECRET, { expiresIn: '7d' });
  res.json({ message: 'Đăng ký thành công', token, user: newUser });
});

app.post('/api/auth/login', (req, res) => {
  const { email, password } = req.body;
  const user = memoryStore.users.find(u => u.email.toLowerCase() === email.toLowerCase());
  if (!user) return res.status(401).json({ error: 'Tài khoản hoặc mật khẩu không chính xác' });
  if (user.is_locked) return res.status(403).json({ error: 'Tài khoản đã bị khóa do vi phạm an toàn gian lận' });

  const token = jwt.sign({ id: user.id, email: user.email, role: user.role }, JWT_SECRET, { expiresIn: '7d' });
  res.json({ message: 'Đăng nhập thành công', token, user });
});

// KYC Upload Endpoint
app.post('/api/auth/kyc-upload', authenticate, (req, res) => {
  const { doc_type, doc_number, front_image_url, back_image_url } = req.body;
  const kycRecord = {
    id: 'kyc_' + Math.random().toString(36).substring(2, 9),
    user_id: req.user.id,
    doc_type: doc_type || 'CCCD',
    doc_number,
    front_image_url,
    back_image_url,
    status: 'pending',
    submitted_at: new Date().toISOString()
  };
  memoryStore.kycDocs.push(kycRecord);
  res.json({ message: 'Đã tải lên hồ sơ KYC thành công. Đang chờ Admin duyệt.', kycRecord });
});

// ==========================================================================
// 2. CAMPAIGN SERVICE (CRUD & State Machine)
// ==========================================================================
// State Machine: draft -> pending_review -> active -> funded/failed -> closed
app.get('/api/campaigns', (req, res) => {
  res.json({ projects: memoryStore.projects });
});

app.get('/api/campaigns/:id', (req, res) => {
  const project = memoryStore.projects.find(p => p.id === req.params.id);
  if (!project) return res.status(404).json({ error: 'Không tìm thấy dự án' });
  res.json({ project });
});

app.post('/api/campaigns', authenticate, (req, res) => {
  const { name, category, description, target_amount, location_name, lat, lng, milestones } = req.body;

  const newProject = {
    id: 'proj_' + Math.random().toString(36).substring(2, 9),
    owner_id: req.user.id,
    name,
    category,
    icon: '🌱',
    cover: 'cover-a',
    description,
    location_name,
    target_amount: parseFloat(target_amount),
    raised_amount: 0,
    status: 'pending_review', // State Machine initial state after submit
    lat: lat || 10.7769,
    lng: lng || 106.7009,
    creator_name: req.user.email,
    milestones: milestones || [],
    created_at: new Date().toISOString()
  };

  memoryStore.projects.push(newProject);

  // Trigger Async Background AI-Flag Scanner (Non-blocking!)
  runAsyncAIFlagCheck(newProject.id, newProject.name, newProject.description);

  res.status(201).json({
    message: 'Tạo dự án thành công. Dự án đang ở trạng thái pending_review để AI kiểm tra & Admin duyệt.',
    project: newProject
  });
});

// ==========================================================================
// 3. PAYMENT & ESCROW SERVICE (Webhook & Ledger)
// ==========================================================================
// Webhook endpoint simulating MoMo / VNPay IPN Callback
app.post('/api/payments/momo-webhook', (req, res) => {
  const { projectId, amount, backerName, gatewayTxnId } = req.body;

  const project = memoryStore.projects.find(p => p.id === projectId);
  if (!project) return res.status(404).json({ error: 'Dự án không tồn tại' });

  const depositAmount = parseFloat(amount);
  project.raised_amount += depositAmount;

  // Check state transition to 'funded'
  if (project.raised_amount >= project.target_amount && project.status === 'active') {
    project.status = 'funded';
  }

  // Record into Escrow Internal Ledger
  const ledgerEntry = {
    id: 'tx_' + Math.random().toString(36).substring(2, 9),
    project_id: projectId,
    user_name: backerName || 'Nhà tài trợ ẩn danh',
    amount: depositAmount,
    type: 'escrow_deposit', // Money held in Escrow account
    gateway: 'momo',
    gateway_txn_id: gatewayTxnId || 'MOMO_' + Date.now(),
    description: `+${depositAmount.toLocaleString('vi-VN')}đ từ ${backerName || 'Backer'} (Ký quỹ Escrow)`,
    created_at: new Date().toISOString()
  };
  memoryStore.ledger.push(ledgerEntry);

  // Realtime Live Feed Event Push via Socket.io
  broadcastLiveFeed('NEW_TRANSACTION', {
    projectId,
    projectName: project.name,
    backerName: ledgerEntry.user_name,
    amount: depositAmount,
    raisedTotal: project.raised_amount,
    targetTotal: project.target_amount
  });

  res.json({ status: 'success', message: 'Ghi nhận đóng góp Escrow thành công', ledgerEntry });
});

// ==========================================================================
// 4. LOCATION SERVICE (Geofencing 3-5km Radius)
// ==========================================================================
app.get('/api/location/nearby', (req, res) => {
  const lat = parseFloat(req.query.lat) || 10.7769; // Default HCM Q1
  const lng = parseFloat(req.query.lng) || 106.7009;
  const radiusKm = parseFloat(req.query.radius) || 5.0; // Default 5km

  const nearby = memoryStore.projects.filter(p => {
    const distance = haversineKm(lat, lng, p.lat, p.lng);
    p.distanceKm = Math.round(distance * 10) / 10;
    return distance <= radiusKm;
  });

  res.json({ lat, lng, radiusKm, count: nearby.length, projects: nearby });
});

// ==========================================================================
// 5. AI-FLAG SERVICE (Async Background Worker)
// ==========================================================================
function runAsyncAIFlagCheck(projectId, name, description) {
  setTimeout(() => {
    // Simulated Zero-Cost Image & Text NLP Fraud Check
    const suspiciousKeywords = ['lừa đảo', 'gấp lắm', 'chuyển khoản cá nhân', 'crypto', 'copy'];
    let fraudScore = 5;
    const reasons = [];

    suspiciousKeywords.forEach(word => {
      if (description.toLowerCase().includes(word)) {
        fraudScore += 30;
        reasons.push(`Phát hiện từ khóa rủi ro: "${word}"`);
      }
    });

    const isSuspicious = fraudScore > 50;
    const flagRecord = {
      id: 'flag_' + Math.random().toString(36).substring(2, 9),
      project_id: projectId,
      fraud_score: fraudScore,
      is_suspicious: isSuspicious,
      reasons: reasons.length > 0 ? reasons : ['Nội dung minh bạch', 'Hình ảnh gốc hợp lệ'],
      created_at: new Date().toISOString()
    };
    memoryStore.aiFlags.push(flagRecord);

    console.log(`🤖 [AI-Flag Background Worker] Project ${projectId} checked. Fraud Score: ${fraudScore}%`);
  }, 1000);
}

app.get('/api/ai-flag/:projectId', (req, res) => {
  const flag = memoryStore.aiFlags.find(f => f.project_id === req.params.projectId);
  res.json({ flag: flag || { fraud_score: 0, is_suspicious: false, reasons: ['Chưa ghi nhận rủi ro'] } });
});

// ==========================================================================
// 6. ADMIN & MODERATION SERVICE
// ==========================================================================
app.get('/api/admin/pending-projects', authenticate, requireRole('admin'), (req, res) => {
  const pending = memoryStore.projects.filter(p => p.status === 'pending_review');
  res.json({ count: pending.length, projects: pending });
});

app.post('/api/admin/approve-project', authenticate, requireRole('admin'), (req, res) => {
  const { projectId, approve } = req.body;
  const project = memoryStore.projects.find(p => p.id === projectId);
  if (!project) return res.status(404).json({ error: 'Không tìm thấy dự án' });

  project.status = approve ? 'active' : 'closed';
  res.json({ message: `Dự án đã được ${approve ? 'duyệt lên sàn (active)' : 'từ chối (closed)'}`, project });
});

app.post('/api/admin/release-milestone', authenticate, requireRole('admin'), (req, res) => {
  const { projectId, milestoneId } = req.body;
  const project = memoryStore.projects.find(p => p.id === projectId);
  if (!project) return res.status(404).json({ error: 'Không tìm thấy dự án' });

  const milestone = (project.milestones || []).find(m => m.id === milestoneId);
  if (!milestone) return res.status(404).json({ error: 'Không tìm thấy mốc giải ngân' });

  milestone.status = 'released';

  // Record Disbursement in Ledger
  const disbursementTx = {
    id: 'tx_out_' + Math.random().toString(36).substring(2, 9),
    project_id: projectId,
    amount: milestone.target_amount,
    type: 'milestone_release',
    description: `Giải ngân mốc "${milestone.name}" (-${milestone.target_amount.toLocaleString('vi-VN')}đ)`,
    created_at: new Date().toISOString()
  };
  memoryStore.ledger.push(disbursementTx);

  // Emit Live Feed Event
  broadcastLiveFeed('MILESTONE_RELEASED', {
    projectId,
    projectName: project.name,
    milestoneName: milestone.name,
    amount: milestone.target_amount
  });

  res.json({ message: 'Giải ngân mốc thành công!', milestone, disbursementTx });
});

// Start Express + Socket.io Server
server.listen(PORT, () => {
  console.log(`🚀 [LocalVest Backend] Running on http://localhost:${PORT}`);
  console.log(`⚡ [Realtime Live Feed] Socket.io ready!`);
});
