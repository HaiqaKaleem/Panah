import { useState } from 'react'
import { useProject } from '../context/ProjectContext'
import Viewport3D from '../components/viewport/Viewport3D'
import MaterialInputs from '../components/build/MaterialInputs'
import CompliancePrescreen from '../components/build/CompliancePrescreen'
import StructuralAnalysis from '../components/build/StructuralAnalysis'
import LoadingSpinner from '../components/common/LoadingSpinner'
import ErrorAlert from '../components/common/ErrorAlert'

export default function BuildPage() {
  const {
    activeProject,
    activeDesign,
    activeGeometry,
    generatedDesigns,
    selectDesign,
    constraintSet,
    generateDesignsWithConstraints,
    generating,
    loading,
    error,
  } = useProject()

  const [currentMaterials, setCurrentMaterials] = useState(constraintSet?.materials || [])

  const handleUpdateMaterials = (updatedMats) => {
    setCurrentMaterials(updatedMats)
  }

  const handleReGenerate = async () => {
    await generateDesignsWithConstraints({ materials: currentMaterials }, 2)
  }

  if (loading && !activeDesign) {
    return (
      <div className="page">
        <LoadingSpinner message="Connecting to generative design engine..." />
      </div>
    )
  }

  const activeDesignName = activeDesign?.version || (generatedDesigns?.[0]?.version) || 'Module Alpha - 1'
  const modelId = activeDesign?.candidate_id ? `TSU-SH-${activeDesign.candidate_id}` : 'TSU-SH-042-B'

  return (
    <div className="page">
      <div className="page-head">
        <h1>PARAMETRIC DESIGN ENGINE</h1>
        <div className="page-sub">
          PROJECT: {activeProject?.name?.toUpperCase() || 'PANAH_SHELTER'} // REAL-TIME LOAD DISTRIBUTION, MATERIAL CONSTRAINTS, AND SPHERE VALIDATION
        </div>
      </div>

      <ErrorAlert message={error} />

      {/* Candidate Switcher if multiple designs exist */}
      {generatedDesigns && generatedDesigns.length > 1 && (
        <div style={{ display: 'flex', gap: '8px', marginBottom: '16px', alignItems: 'center' }}>
          <span style={{ fontSize: '11px', color: '#9aa39a', letterSpacing: '0.08em', fontWeight: 600 }}>
            DESIGN CANDIDATES:
          </span>
          {generatedDesigns.map((d, index) => {
            const isSelected = activeDesign?.id === d.id || (!activeDesign && index === 0)
            return (
              <button
                key={d.id}
                onClick={() => selectDesign(d.id)}
                style={{
                  background: isSelected ? '#2e7d46' : '#141c17',
                  border: isSelected ? '1px solid #4caf50' : '1px solid #223328',
                  color: isSelected ? '#fff' : '#9aa39a',
                  padding: '6px 12px',
                  borderRadius: '4px',
                  fontSize: '12px',
                  fontWeight: 600,
                  cursor: 'pointer',
                }}
              >
                {d.version || `Option ${index + 1}`} ({Math.round(d.overall_integrity_score || d.score || 78)}% score)
              </button>
            )
          })}
        </div>
      )}

      <div className="build-grid">
        <div className="build-left">
          {/* 3D WebGL Parametric Viewport */}
          <Viewport3D
            geometryData={activeGeometry}
            activeDesignName={activeDesignName}
            modelId={modelId}
          />

          {/* Dynamic Material Input & Constraints */}
          <MaterialInputs
            constraintSet={constraintSet}
            onUpdateMaterials={handleUpdateMaterials}
            onGenerate={handleReGenerate}
            generating={generating}
          />
        </div>

        <div className="build-right">
          {/* Compliance Prescreen Checklist */}
          <CompliancePrescreen designDetail={activeDesign} />

          {/* Structural Analysis, Deflection Curve & PDF Report */}
          <StructuralAnalysis
            designDetail={activeDesign}
            projectName={activeProject?.name || 'Panagah Shelter'}
          />
        </div>
      </div>
    </div>
  )
}
