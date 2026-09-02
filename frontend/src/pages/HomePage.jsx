import { useState } from 'react'
import {
  Plus, FolderOpen, CheckCircle2, AlertTriangle, SquarePen,
  SquareKanban, CirclePlus, X
} from 'lucide-react'
import { useProject } from '../context/ProjectContext'
import heroImg from '../assets/hero.png'
import cardAlpha from '../assets/card-alpha.png'
import cardBeta from '../assets/card-beta.png'

export default function HomePage({ onBuild, onProjects, onHistory }) {
  const { projects, selectProject, createNewProject, loading } = useProject()
  const [showNewModal, setShowNewModal] = useState(false)
  const [projectName, setProjectName] = useState('')
  const [projectLoc, setProjectLoc] = useState('')
  const [creating, setCreating] = useState(false)

  const handleStartNew = async (e) => {
    e.preventDefault()
    setCreating(true)
    try {
      await createNewProject({
        name: projectName || 'Humanitarian Shelter Build',
        location: projectLoc || 'South Asia Regional Site',
      })
      setShowNewModal(false)
      onBuild()
    } catch (err) {
      console.warn('Failed to start new build:', err)
    } finally {
      setCreating(false)
    }
  }

  const handleEditProject = async (projectId) => {
    await selectProject(projectId)
    onBuild()
  }

  return (
    <div className="home">
      <section className="hero" style={{ backgroundImage: `url(${heroImg})` }}>
        <h1 className="hero-title">PANAH</h1>
        <p className="hero-sub">AI-Generated, Locally-Adapted, Structurally-Validated Shelter Designs</p>
        <div className="hero-actions">
          <button className="btn-green" onClick={() => setShowNewModal(true)}>
            <Plus size={16} /> START NEW BUILD
          </button>
          <button className="btn-dark" onClick={onProjects}>
            <FolderOpen size={16} /> VIEW SAVED PROJECTS
          </button>
        </div>
      </section>

      <section className="recent">
        <div className="recent-head">
          <h2>Recent Active Projects</h2>
          <button className="link-rust" onClick={onHistory}>
            VIEW FULL HISTORY →
          </button>
        </div>

        <div className="project-cards">
          {projects && projects.length > 0 ? (
            projects.slice(0, 2).map((proj, idx) => {
              const isFirst = idx === 0
              const thumbnail = isFirst ? cardAlpha : cardBeta
              const isReviewReq = idx % 2 === 1

              return (
                <article className="project-card" key={proj.id}>
                  <div className="pc-media">
                    {isReviewReq ? (
                      <span className="badge badge-amber">
                        <AlertTriangle size={13} /> REVIEW REQ.
                      </span>
                    ) : (
                      <span className="badge badge-green">
                        <CheckCircle2 size={13} /> VALIDATED
                      </span>
                    )}
                    <img src={thumbnail} alt={proj.name} />
                  </div>
                  <div className="pc-body">
                    <h3>{proj.name}</h3>
                    <div className="pc-id">#PRJ-{proj.id}-A</div>
                    <div className="pc-stats">
                      <div className="pc-stat">
                        <div className="pc-stat-label">LOCATION</div>
                        <div className="pc-stat-value">{proj.location || 'Regional Zone'}</div>
                      </div>
                      <div className="pc-stat">
                        <div className="pc-stat-label">LOAD EST.</div>
                        <div className="pc-stat-value">450 kg/m²</div>
                      </div>
                    </div>
                  </div>
                  <div className="pc-footer">
                    <button onClick={() => handleEditProject(proj.id)}>
                      <SquarePen size={14} /> Edit
                    </button>
                    <button onClick={() => handleEditProject(proj.id)}>
                      <SquareKanban size={14} /> Analyze
                    </button>
                  </div>
                </article>
              )
            })
          ) : loading ? (
            <div style={{ color: '#8b949b', padding: '24px' }}>Loading active builds...</div>
          ) : null}

          <article
            className="project-card new-schematic"
            onClick={() => setShowNewModal(true)}
            style={{ cursor: 'pointer' }}
          >
            <CirclePlus size={30} className="ns-icon" />
            <h3>New Schematic</h3>
            <p>Initialize blank canvas or import topographic survey data.</p>
          </article>
        </div>
      </section>

      {/* New Project Modal */}
      {showNewModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.75)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
          padding: '16px',
        }}>
          <div style={{
            background: '#141c17',
            border: '1px solid #2e4436',
            borderRadius: '8px',
            maxWidth: '480px',
            width: '100%',
            padding: '24px',
            position: 'relative',
          }}>
            <button
              onClick={() => setShowNewModal(false)}
              style={{ position: 'absolute', top: '16px', right: '16px', background: 'none', border: 'none', color: '#8b949b', cursor: 'pointer' }}
            >
              <X size={18} />
            </button>
            <h2 style={{ color: '#fff', fontSize: '18px', marginBottom: '16px', fontWeight: 600 }}>
              START NEW SHELTER PROJECT
            </h2>
            <form onSubmit={handleStartNew} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: '#9aa39a', marginBottom: '4px', textTransform: 'uppercase' }}>
                  Project Name / Module Identifier
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Rapid Truss Shelter Mk IV"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  style={{
                    width: '100%',
                    background: '#0c120f',
                    border: '1px solid #223328',
                    borderRadius: '4px',
                    padding: '8px 12px',
                    color: '#fff',
                    fontSize: '13px',
                  }}
                />
              </div>
              <div>
                <label style={{ display: 'block', fontSize: '11px', color: '#9aa39a', marginBottom: '4px', textTransform: 'uppercase' }}>
                  Deployment Location / Hazard Region
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Khyber Pakhtunkhwa, Pakistan"
                  value={projectLoc}
                  onChange={(e) => setProjectLoc(e.target.value)}
                  style={{
                    width: '100%',
                    background: '#0c120f',
                    border: '1px solid #223328',
                    borderRadius: '4px',
                    padding: '8px 12px',
                    color: '#fff',
                    fontSize: '13px',
                  }}
                />
              </div>
              <button
                type="submit"
                className="btn-green"
                disabled={creating}
                style={{ padding: '10px', marginTop: '6px' }}
              >
                {creating ? 'INITIALIZING PARAMETRIC PIPELINE...' : 'INITIALIZE BUILD'}
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
