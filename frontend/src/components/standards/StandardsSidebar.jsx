import { useState } from 'react'
import { Search, ChevronRight, ChevronDown } from 'lucide-react'

export default function StandardsSidebar({
  categories: _categories = [],
  rules = [],
  selectedRuleId,
  onSelectRule,
  searchQuery,
  onSearchChange,
}) {
  const [openCategories, setOpenCategories] = useState({ wind: true, materials: true, shelter: true })

  const toggleCategory = (cat) => {
    setOpenCategories((prev) => ({ ...prev, [cat]: !prev[cat] }))
  }

  // Filter rules by search query if present
  const filteredRules = searchQuery
    ? rules.filter((r) =>
        (r.name || r.rule_id || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
        (r.description || '').toLowerCase().includes(searchQuery.toLowerCase())
      )
    : rules

  // Group rules by category
  const groupedRules = {}
  filteredRules.forEach((r) => {
    const cat = r.category || 'shelter'
    if (!groupedRules[cat]) groupedRules[cat] = []
    groupedRules[cat].push(r)
  })

  return (
    <aside className="card std-sidebar">
      <div className="std-side-head">
        <div className="std-handbook">SPHERE HANDBOOK V24.1</div>
        <label className="std-search">
          <Search size={13} />
          <input
            placeholder="Search documentation..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
          />
        </label>
      </div>

      <div className="std-tree">
        {Object.entries(groupedRules).length === 0 ? (
          <div style={{ padding: '16px', color: '#687768', fontSize: '12px' }}>
            No matching standards found
          </div>
        ) : (
          Object.entries(groupedRules).map(([category, catRules]) => {
            const isOpen = openCategories[category] !== false
            return (
              <div className="tree-group" key={category}>
                <div
                  className={`tree-root ${isOpen ? 'open' : ''}`}
                  onClick={() => toggleCategory(category)}
                  style={{ cursor: 'pointer' }}
                >
                  {isOpen ? <ChevronDown size={13} /> : <ChevronRight size={13} />}
                  <span style={{ textTransform: 'capitalize' }}>
                    {category.replace(/_/g, ' ')} Standards ({catRules.length})
                  </span>
                </div>
                {isOpen && (
                  <div className="tree-children">
                    {catRules.map((rule) => {
                      const isSelected = selectedRuleId === rule.id || selectedRuleId === rule.rule_id
                      return (
                        <div
                          key={rule.id || rule.rule_id}
                          className={`tree-leaf ${isSelected ? 'active' : ''}`}
                          onClick={() => onSelectRule(rule.id || rule.rule_id)}
                          style={{ cursor: 'pointer' }}
                        >
                          {rule.name || rule.rule_id} {isSelected && <i>•</i>}
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })
        )}
      </div>
    </aside>
  )
}
