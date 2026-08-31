import { useState, useEffect } from 'react'
import { ClipboardCheck, Plus, XCircle, AlertTriangle } from 'lucide-react'
import { materialsApi } from '../../api/materials'

export default function MaterialInputs({ constraintSet, onUpdateMaterials, onGenerate, generating }) {
  const [catalog, setCatalog] = useState([])
  const [showCatalogModal, setShowCatalogModal] = useState(false)
  const [materials, setMaterials] = useState(constraintSet?.materials || [])

  useEffect(() => {
    if (constraintSet?.materials) {
      setMaterials(constraintSet.materials)
    }
  }, [constraintSet])

  useEffect(() => {
    materialsApi.getCatalog().then((res) => {
      if (res && res.materials) setCatalog(res.materials)
    }).catch((err) => console.warn('Catalog fetch error:', err))
  }, [])

  const handleQtyChange = (id, newQty) => {
    const updated = materials.map((m) =>
      m.id === id ? { ...m, qty: Number(newQty) || 0 } : m
    )
    setMaterials(updated)
    if (onUpdateMaterials) onUpdateMaterials(updated)
  }

  const handleAddMaterial = (catMat) => {
    const newId = `MAT-${catMat.code || catMat.material_type?.slice(0, 3).toUpperCase() || 'NEW'}-${Date.now().toString().slice(-2)}`
    const newEntry = {
      id: newId,
      type: catMat.material_type || catMat.type || 'treated_bamboo',
      qty: 20,
      length_m: catMat.max_length_m || 3.0,
      diameter_m: (catMat.standard_diameters_mm?.[0] || 80) / 1000,
    }
    const updated = [...materials, newEntry]
    setMaterials(updated)
    if (onUpdateMaterials) onUpdateMaterials(updated)
    setShowCatalogModal(false)
  }

  const handleRemoveMaterial = (id) => {
    const updated = materials.filter((m) => m.id !== id)
    setMaterials(updated)
    if (onUpdateMaterials) onUpdateMaterials(updated)
  }

  // Split into Structural Core vs Cladding/Foundation
  const structuralCore = materials.filter((m) =>
    ['treated_bamboo', 'reclaimed_timber', 'steel_connector', 'structural'].some((k) => (m.type || '').includes(k))
  )
  const claddingAndFoundation = materials.filter((m) => !structuralCore.includes(m))

  // Find constraint warnings
  const bambooItem = materials.find((m) => (m.type || '').includes('bamboo'))
  const hasSpanWarning = bambooItem && (bambooItem.length_m || 3) < 4.0

  return (
    <section className="card material-card">
      <div className="material-head">
        <div className="card-title">
          <ClipboardCheck size={18} /> Material Input &amp; Constraints
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn-black" onClick={() => setShowCatalogModal(true)}>
            <Plus size={14} /> ADD MATERIAL
          </button>
          <button
            className="btn-green"
            onClick={onGenerate}
            disabled={generating}
            style={{ fontSize: '11px', padding: '6px 12px' }}
          >
            {generating ? 'RE-SOLVING...' : 'RE-GENERATE DESIGN'}
          </button>
        </div>
      </div>

      <div className="material-body">
        {/* Structural Core Column */}
        <div className="mat-col">
          <div className="mat-col-head">STRUCTURAL CORE</div>
          {structuralCore.length === 0 ? (
            <div style={{ padding: '12px', fontSize: '12px', color: '#687768' }}>No core structural materials</div>
          ) : (
            structuralCore.map((m) => (
              <div className="mat-row" key={m.id}>
                <div className="mat-row-top">
                  <span className="mat-name">{m.type ? m.type.replace(/_/g, ' ').toUpperCase() : 'BAMBOO CULM'}</span>
                  <span className="mat-code">{m.id}</span>
                </div>
                <div className="mat-row-bottom">
                  <input
                    className="mat-qty"
                    type="number"
                    value={m.qty}
                    onChange={(e) => handleQtyChange(m.id, e.target.value)}
                  />
                  <span className="mat-unit">pcs ({m.length_m || 3}m)</span>
                  <button
                    onClick={() => handleRemoveMaterial(m.id)}
                    style={{ background: 'transparent', border: 'none', color: '#8b949b', cursor: 'pointer', marginLeft: 'auto' }}
                  >
                    ×
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Cladding & Foundation Column */}
        <div className="mat-col bordered">
          <div className="mat-col-head">CLADDING &amp; FOUNDATION</div>
          {claddingAndFoundation.length === 0 ? (
            <div style={{ padding: '12px', fontSize: '12px', color: '#687768' }}>No cladding or foundation items</div>
          ) : (
            claddingAndFoundation.map((m) => (
              <div className="mat-row" key={m.id}>
                <div className="mat-row-top">
                  <span className="mat-name">{m.type ? m.type.replace(/_/g, ' ').toUpperCase() : 'CLADDING'}</span>
                  <span className="mat-code">{m.id}</span>
                </div>
                <div className="mat-row-bottom">
                  <input
                    className="mat-qty"
                    type="number"
                    value={m.qty}
                    onChange={(e) => handleQtyChange(m.id, e.target.value)}
                  />
                  <span className="mat-unit">units / sq.m</span>
                  <button
                    onClick={() => handleRemoveMaterial(m.id)}
                    style={{ background: 'transparent', border: 'none', color: '#8b949b', cursor: 'pointer', marginLeft: 'auto' }}
                  >
                    ×
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Warnings */}
        <div className="mat-warn-col">
          <div className="mat-warn">
            <XCircle size={17} className="mat-warn-x" />
            <AlertTriangle size={18} className="mat-warn-icon" />
            <div>
              <div className="mat-warn-title">Material Constraint Engine</div>
              <p>
                {hasSpanWarning
                  ? `Active bamboo stock (${bambooItem.length_m}m) requires multi-bay king-post support for ridge spans exceeding 4.0m.`
                  : 'All dimensional limits satisfied for current span and seismic zone.'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Catalog Modal */}
      {showCatalogModal && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0,0,0,0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1001,
          padding: '16px',
        }}>
          <div style={{
            background: '#141c17',
            border: '1px solid #2e4436',
            borderRadius: '8px',
            maxWidth: '560px',
            width: '100%',
            padding: '20px',
            maxHeight: '80vh',
            overflowY: 'auto',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ color: '#fff', margin: 0, fontSize: '16px' }}>REGIONAL MATERIAL CATALOG</h3>
              <button onClick={() => setShowCatalogModal(false)} style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer' }}>✕</button>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {catalog.map((catMat) => (
                <div
                  key={catMat.material_type || catMat.name}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    background: '#0c120f',
                    padding: '10px 14px',
                    borderRadius: '4px',
                    border: '1px solid #223328',
                  }}
                >
                  <div>
                    <div style={{ fontWeight: 600, color: '#f0f3f0', fontSize: '13px' }}>{catMat.display_name || catMat.name || catMat.material_type}</div>
                    <div style={{ fontSize: '11px', color: '#8b949b' }}>
                      Category: {catMat.category} • Cost: ${catMat.unit_cost_usd || 0.8} / {catMat.cost_unit || 'unit'}
                    </div>
                  </div>
                  <button
                    className="btn-green"
                    onClick={() => handleAddMaterial(catMat)}
                    style={{ fontSize: '11px', padding: '4px 10px' }}
                  >
                    Select
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
