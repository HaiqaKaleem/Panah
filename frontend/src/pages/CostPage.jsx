import { useState, useEffect } from 'react'
import { useProject } from '../context/ProjectContext'
import { bomApi } from '../api/bom'
import CostMatrix from '../components/cost/CostMatrix'
import EfficiencyStats from '../components/cost/EfficiencyStats'
import DeploymentScale from '../components/cost/DeploymentScale'
import LoadingSpinner from '../components/common/LoadingSpinner'

export default function CostPage() {
  const { activeProject, activeSite, activeDesign } = useProject()
  const [bomData, setBomData] = useState(null)
  const [loadingBom, setLoadingBom] = useState(false)

  useEffect(() => {
    if (activeProject && activeSite && activeDesign) {
      setLoadingBom(true)
      bomApi.getBOM(activeProject.id, activeSite.id, activeDesign.id)
        .then((res) => setBomData(res))
        .catch((err) => console.warn('BOM fetch error:', err))
        .finally(() => setLoadingBom(false))
    }
  }, [activeProject, activeSite, activeDesign])

  const totalUnitCost = bomData?.summary?.total_cost_usd || 84.60
  const lineItems = bomData?.line_items || []
  const costPerM2 = (totalUnitCost / 30.0).toFixed(2)

  // Calculate local sourcing percentage
  const localItems = lineItems.filter((i) => i.local_availability === 'on-site')
  const localRatio = lineItems.length > 0
    ? Math.round((localItems.length / lineItems.length) * 100)
    : 72

  return (
    <div className="page">
      <div className="page-head row">
        <div>
          <h1>COST ESTIMATION MODULE</h1>
          <div className="page-sub">
            PROJECT: {activeProject?.name?.toUpperCase() || 'PANAH_SHELTER_V2'} // PHASE: PRE-DEPLOYMENT
          </div>
        </div>
        <div className="total-card">
          <div className="total-label">ESTIMATED TOTAL</div>
          <div className="total-price">
            ${Number(totalUnitCost).toFixed(2)} <span>/ unit</span>
          </div>
        </div>
      </div>

      {loadingBom && !bomData ? (
        <LoadingSpinner message="Calculating material cost matrix and local supply footprint..." />
      ) : (
        <div className="cost-grid">
          {/* Local Market Cost Matrix */}
          <CostMatrix
            bomItems={lineItems}
            onAddLogistics={() => alert('Logistics overhead added to estimation model.')}
          />

          {/* Efficiency Analytics & Pareto Frontier Curve */}
          <section className="card cost-card">
            <EfficiencyStats
              costPerM2={costPerM2}
              structRating={94}
              localSourcingRatio={localRatio}
            />
          </section>

          {/* Deployment Scale & Auditable BOM Exporter */}
          <DeploymentScale
            unitCost={totalUnitCost}
            bambooPerUnit={24}
            tinPerUnit={12}
            projectId={activeProject?.id}
            siteId={activeSite?.id}
            designId={activeDesign?.id}
          />
        </div>
      )}
    </div>
  )
}
