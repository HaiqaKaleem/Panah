import { useState, useEffect } from 'react'
import { Link2, Printer, Download } from 'lucide-react'
import { standardsApi } from '../api/standards'
import StandardsSidebar from '../components/standards/StandardsSidebar'
import StandardsContent from '../components/standards/StandardsContent'
import LoadingSpinner from '../components/common/LoadingSpinner'

export default function StandardsPage() {
  const [categories, setCategories] = useState([])
  const [rules, setRules] = useState([])
  const [selectedRuleId, setSelectedRuleId] = useState(null)
  const [ruleDetail, setRuleDetail] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)

  // Fetch categories and rules on mount
  useEffect(() => {
    const fetchStandards = async () => {
      setLoading(true)
      try {
        const [catRes, rulesRes] = await Promise.allSettled([
          standardsApi.getCategories(),
          standardsApi.getRules(),
        ])

        const catList = catRes.status === 'fulfilled' ? catRes.value?.categories || [] : []
        const ruleList = rulesRes.status === 'fulfilled' ? rulesRes.value?.rules || [] : []

        setCategories(catList)
        setRules(ruleList)

        if (ruleList.length > 0) {
          const firstRule = ruleList[0]
          setSelectedRuleId(firstRule.id || firstRule.rule_id)
          setRuleDetail(firstRule)
        }
      } catch (err) {
        console.warn('Error fetching standards:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchStandards()
  }, [])

  // When a rule is selected, fetch its detail
  const handleSelectRule = async (ruleId) => {
    setSelectedRuleId(ruleId)
    try {
      const detail = await standardsApi.getRuleDetail(ruleId)
      setRuleDetail(detail)
    } catch {
      // Fallback to local rule object in list
      const fallback = rules.find((r) => r.id === ruleId || r.rule_id === ruleId)
      if (fallback) setRuleDetail(fallback)
    }
  }

  const handlePrint = () => {
    window.print()
  }

  return (
    <div className="page">
      <div className="page-head row">
        <div>
          <h1>GUIDELINE &amp; STANDARDS</h1>
          <div className="page-sub">SPHERE HANDBOOK &amp; ENGINEERING REFERENCE MANUAL</div>
        </div>
        <div className="std-actions">
          <button title="Copy Link" onClick={() => navigator.clipboard?.writeText(window.location.href)}>
            <Link2 size={16} />
          </button>
          <button title="Print Manual" onClick={handlePrint}>
            <Printer size={16} />
          </button>
          <button title="Export Standard Document" onClick={handlePrint}>
            <Download size={16} />
          </button>
        </div>
      </div>

      {loading && rules.length === 0 ? (
        <LoadingSpinner message="Loading Sphere Handbook standard specifications..." />
      ) : (
        <div className="std-grid">
          <StandardsSidebar
            categories={categories}
            rules={rules}
            selectedRuleId={selectedRuleId}
            onSelectRule={handleSelectRule}
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
          />

          <StandardsContent ruleDetail={ruleDetail} />
        </div>
      )}
    </div>
  )
}
