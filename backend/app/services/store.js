/* ==========================================================================
   LocalVest — Hybrid Data Store (Memory / SQLite / Supabase PostgreSQL)
   Designed by Backend Architect for 0-Cost Student Deployment.
   Runs instantly locally without setup, switches to PostgreSQL via DATABASE_URL.
   ========================================================================== */

const { Pool } = require('pg');
require('dotenv').config();

let pool = null;
if (process.env.DATABASE_URL) {
  pool = new Pool({
    connectionString: process.env.DATABASE_URL,
    ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false
  });
}

// In-Memory Seed Data Fallback for Zero-Config Local Dev
const memoryStore = {
  users: [
    {
      id: 'usr_admin',
      email: 'admin@localvest.vn',
      full_name: 'System Admin',
      role: 'admin',
      kyc_status: 'approved',
      is_locked: false
    },
    {
      id: 'usr_demo',
      email: 'demo@localvest.vn',
      full_name: 'Nguyễn Văn Demo',
      role: 'backer',
      kyc_status: 'approved',
      is_locked: false
    }
  ],
  projects: [
    {
      id: 'proj_1',
      name: 'Phòng học miễn phí cho trẻ em xóm trọ',
      category: 'Giáo dục',
      icon: '🎓',
      cover: 'cover-a',
      location_name: 'Phường Bình Hưng Hoà, Q. Bình Tân',
      target_amount: 30000000,
      raised_amount: 21000000,
      status: 'active',
      lat: 10.7889,
      lng: 106.6809,
      description: 'Cải tạo một phòng sinh hoạt cộng đồng thành lớp học miễn phí buổi tối cho trẻ em xóm trọ.',
      creator_name: 'Nguyễn Thị Mai',
      creator_verified: true,
      milestones: [
        { id: 'm1', name: 'Sửa chữa phòng học, lắp bàn ghế', target_amount: 12000000, status: 'released', description: 'Đã giải ngân' },
        { id: 'm2', name: 'Mua sách vở, dụng cụ học tập', target_amount: 8000000, status: 'released', description: 'Đã giải ngân' },
        { id: 'm3', name: 'Duy trì chi phí điện nước 6 tháng', target_amount: 10000000, status: 'locked', description: 'Chờ giải ngân' }
      ]
    },
    {
      id: 'proj_2',
      name: 'Trạm tái chế nhựa khu phố 4',
      category: 'Môi trường',
      icon: '♻️',
      cover: 'cover-b',
      location_name: 'Phường Tân Định, Q.1',
      target_amount: 45000000,
      raised_amount: 45000000,
      status: 'funded',
      lat: 10.7689,
      lng: 106.7109,
      description: 'Lắp đặt trạm thu gom và phân loại rác nhựa tự động kết nối đơn vị tái chế.',
      creator_name: 'Trần Văn Khoa',
      creator_verified: true,
      milestones: [
        { id: 'm4', name: 'Mua thùng phân loại', target_amount: 25000000, status: 'released', description: 'Đã hoàn thành' },
        { id: 'm5', name: 'Lắp mái che', target_amount: 10000000, status: 'released', description: 'Đã hoàn thành' },
        { id: 'm6', name: 'Vận hành thử 3 tháng', target_amount: 10000000, status: 'released', description: 'Đã hoàn thành' }
      ]
    }
  ],
  ledger: [
    {
      id: 'tx_1',
      project_id: 'proj_1',
      user_name: 'Trần Văn A',
      amount: 500000,
      type: 'escrow_deposit',
      gateway: 'momo',
      description: '+500.000đ từ Trần Văn A (Ký quỹ Escrow)',
      created_at: new Date().toISOString()
    }
  ],
  aiFlags: [
    {
      id: 'flag_1',
      project_id: 'proj_1',
      fraud_score: 12,
      is_suspicious: false,
      reasons: ['Nội dung nguyên bản', 'Hình ảnh thực tế xác thực']
    }
  ],
  kycDocs: []
};

// Haversine Radius Math (3-5km Radius)
function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

module.exports = {
  pool,
  memoryStore,
  haversineKm
};
