import { useState } from 'react'
import {
  CircleUser, ShieldCheck, Bell, Palette, LifeBuoy, Phone,
  Save, Briefcase, Mail, CheckCircle2, LogIn
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'

const SETTINGS_TABS = [
  { id: 'profile', label: 'Profile', icon: CircleUser },
  { id: 'security', label: 'Security & Auth', icon: ShieldCheck },
  { id: 'notifications', label: 'Notifications', icon: Bell },
  { id: 'appearance', label: 'Appearance', icon: Palette },
]

export default function SettingsPage({ onOpenAuth }) {
  const { user, updateProfile, isAuthenticated } = useAuth()
  const [activeTab, setActiveTab] = useState('profile')
  const [savedSuccess, setSavedSuccess] = useState(false)

  const [formData, setFormData] = useState({
    full_name: user?.full_name || 'Dr. Aris Thorne',
    email: user?.email || 'a.thorne@system-core.net',
    contact: user?.contact || '+92 300 1234567',
    designation: user?.role === 'admin' ? 'Lead Administrator' : 'Senior Structural Engineer',
    organization: user?.organization || 'Panah Shelter Systems & Humanitarian Relief',
  })

  const handleChange = (field, val) => {
    setFormData((prev) => ({ ...prev, [field]: val }))
  }

  const handleSave = (e) => {
    e.preventDefault()
    updateProfile(formData)
    setSavedSuccess(true)
    setTimeout(() => setSavedSuccess(false), 3000)
  }

  return (
    <div className="page">
      <div className="page-head row">
        <div>
          <h1>SYSTEM PREFERENCES</h1>
          <div className="page-sub">SETTINGS AND OPERATIVE IDENTIFICATION</div>
        </div>
        <button className="btn-black big" onClick={handleSave}>
          <Save size={14} /> COMMIT CHANGES
        </button>
      </div>

      {savedSuccess && (
        <div style={{
          background: 'rgba(46, 125, 70, 0.2)',
          border: '1px solid #2e7d46',
          borderRadius: '6px',
          padding: '10px 16px',
          color: '#4caf50',
          fontSize: '13px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '16px',
        }}>
          <CheckCircle2 size={16} /> Preferences successfully updated and synchronized.
        </div>
      )}

      <div className="settings-grid">
        <aside className="card settings-side">
          {SETTINGS_TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              className={`side-item${activeTab === id ? ' active' : ''}`}
              onClick={() => setActiveTab(id)}
            >
              <Icon size={18} /> {label}
            </button>
          ))}
          <div className="side-spacer" />
          <button className="side-item" onClick={() => alert('Panagah Documentation & Engineering Support Portal')}>
            <LifeBuoy size={18} /> Support
          </button>
          <button className="side-item" onClick={() => alert('Regional Field Hotline: +92 51 8842-PANAH')}>
            <Phone size={18} /> Contact Us
          </button>
        </aside>

        <section className="card settings-main">
          {activeTab === 'profile' && (
            <>
              <div className="settings-main-head">
                <div>
                  <h2>Operative Details</h2>
                  <p>Manage your central identification and engineering credentials.</p>
                </div>
                <div className="pic-box">
                  {formData.full_name.split(' ').map((n) => n[0]).join('').slice(0, 2).toUpperCase() || 'OP'}
                </div>
              </div>

              <div className="form-grid">
                <div className="form-field">
                  <label>DESIGNATION / NAME</label>
                  <div className="input-row">
                    <input
                      value={formData.full_name}
                      onChange={(e) => handleChange('full_name', e.target.value)}
                    />
                    <span className="input-icon">
                      <Briefcase size={15} />
                    </span>
                  </div>
                </div>

                <div className="form-field">
                  <label>ROLE / CREDENTIAL</label>
                  <div className="input-row">
                    <input
                      value={formData.designation}
                      onChange={(e) => handleChange('designation', e.target.value)}
                    />
                    <span className="input-icon">
                      <ShieldCheck size={15} />
                    </span>
                  </div>
                </div>

                <div className="form-field">
                  <label>CONTACT INFO</label>
                  <div className="input-row">
                    <input
                      value={formData.contact}
                      onChange={(e) => handleChange('contact', e.target.value)}
                    />
                    <span className="input-icon">
                      <Phone size={15} />
                    </span>
                  </div>
                </div>

                <div className="form-field span2">
                  <label>EMAIL ID</label>
                  <div className="input-row">
                    <input
                      value={formData.email}
                      onChange={(e) => handleChange('email', e.target.value)}
                    />
                    <span className="input-icon">
                      <Mail size={15} />
                    </span>
                  </div>
                </div>

                <div className="form-field span2">
                  <label>ORGANIZATION / RELIEF AGENCY</label>
                  <div className="input-row">
                    <input
                      value={formData.organization}
                      onChange={(e) => handleChange('organization', e.target.value)}
                    />
                    <span className="input-icon">
                      <Briefcase size={15} />
                    </span>
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === 'security' && (
            <div>
              <div className="settings-main-head">
                <div>
                  <h2>Authentication &amp; Security</h2>
                  <p>JWT Session Tokens, OAuth2 verification, and credentials.</p>
                </div>
              </div>

              <div style={{ padding: '12px 0', fontSize: '13px', color: '#c0c8c0', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ background: '#0c120f', padding: '16px', borderRadius: '6px', border: '1px solid #223328' }}>
                  <div style={{ fontWeight: 600, color: '#f0f3f0', marginBottom: '6px' }}>Authentication Status</div>
                  <div>
                    Current Session: {isAuthenticated ? (
                      <span style={{ color: '#4caf50', fontWeight: 600 }}>● Authenticated (JWT Active)</span>
                    ) : (
                      <span style={{ color: '#e67e22' }}>○ Guest Demo Mode</span>
                    )}
                  </div>
                  <div style={{ marginTop: '12px' }}>
                    <button className="btn-green" onClick={onOpenAuth} style={{ fontSize: '12px', padding: '6px 14px' }}>
                      <LogIn size={14} /> Switch / Sign In Account
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div>
              <div className="settings-main-head">
                <div>
                  <h2>Alert Preferences</h2>
                  <p>Configure automated Sphere violation warnings and material bottleneck alerts.</p>
                </div>
              </div>
              <div style={{ padding: '16px 0', display: 'flex', flexDirection: 'column', gap: '12px', color: '#c0c8c0', fontSize: '13px' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <input type="checkbox" defaultChecked /> Real-time Structural Deflection &amp; Wind Shear Warnings
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <input type="checkbox" defaultChecked /> Regional Supply Bottleneck Alerts (&gt;200 units)
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <input type="checkbox" defaultChecked /> Sphere Handbook Compliance Evaluation Reports
                </label>
              </div>
            </div>
          )}

          {activeTab === 'appearance' && (
            <div>
              <div className="settings-main-head">
                <div>
                  <h2>Interface Appearance</h2>
                  <p>Display and viewport rendering mode.</p>
                </div>
              </div>
              <div style={{ padding: '16px 0', color: '#c0c8c0', fontSize: '13px' }}>
                <p><strong>Active Theme:</strong> Tactical Engineering Dark (High Contrast)</p>
                <p><strong>3D Engine:</strong> WebGL Three.js Accelerated</p>
              </div>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}
