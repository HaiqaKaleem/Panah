import { useState, useEffect } from 'react'
import { Search } from 'lucide-react'
import { projectsApi } from '../api/projects'
import { searchApi } from '../api/search'
import { useProject } from '../context/ProjectContext'
import HistoryTable from '../components/history/HistoryTable'
import LoadingSpinner from '../components/common/LoadingSpinner'

export default function HistoryPage({ onNavigateToBuild }) {
  const { selectProject } = useProject()
  const [historyItems, setHistoryItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [searchQuery, setSearchQuery] = useState('')
  const [totalCount, setTotalCount] = useState(0)

  useEffect(() => {
    let isCancelled = false
    const fetchData = async () => {
      setLoading(true)
      try {
        if (searchQuery.trim()) {
          const res = await searchApi.search(searchQuery, 'project')
          if (!isCancelled) {
            const results = res.results || res || []
            setHistoryItems(results.map((r) => ({
              id: r.id || r.entity_id,
              name: r.title || r.name || 'Shelter Build',
              location: r.location || 'South Asia Regional Site',
              created_at: r.created_at,
              status: r.status || 'ITERATING',
              version: r.version || 'v1.0.0',
            })))
            setTotalCount(results.length)
          }
        } else {
          const res = await projectsApi.getHistory()
          if (!isCancelled) {
            const list = res.history || res.projects || (Array.isArray(res) ? res : [])
            setHistoryItems(list.length > 0 ? list : [
              {
                preview: '🏗️', name: 'Bamboo T-Shelter Alpha', id: 'BLD-8942-A',
                location: 'Mindanao, Philippines', date: '2023-10-12', ver: 'v4.2.1', verTone: '',
                status: 'DEPLOYED', statusTone: 'deployed', dot: '●',
              },
              {
                preview: '🏥', name: 'Earthbag Clinic Core', id: 'MED-1105-X',
                location: 'Kathmandu Valley, Nepal', date: '2023-11-04', ver: 'v2.0.8', verTone: 'green',
                status: 'ITERATING', statusTone: 'iterating', dot: '▲',
              },
              {
                preview: '⚡', name: 'Rapid Truss System Mk II', id: 'RF-7721-B',
                location: 'Global Specification', date: '2023-09-18', ver: 'v5.0.0', verTone: '',
                status: 'APPROVED', statusTone: 'approved', dot: '◇',
              },
              {
                preview: '📦', name: 'Timber Frame Mk I', id: 'BLD-1102-O', archived: true,
                location: 'Haiti', date: '2021-02-14', ver: 'v1.0.0', verTone: '',
                status: 'ARCHIVED', statusTone: 'archived', dot: '■',
              },
            ])
            setTotalCount(res.count || list.length || 4)
          }
        }
      } catch (err) {
        console.warn('History fetch error:', err)
      } finally {
        if (!isCancelled) setLoading(false)
      }
    }

    const timer = setTimeout(() => {
      fetchData()
    }, 250)

    return () => {
      isCancelled = true
      clearTimeout(timer)
    }
  }, [searchQuery])

  const handleSelect = async (projectId) => {
    await selectProject(projectId)
    if (onNavigateToBuild) onNavigateToBuild()
  }

  return (
    <div className="page">
      <div className="page-head row">
        <div>
          <h1>PROJECT HISTORY</h1>
          <div className="page-sub">SEARCH THROUGH YOUR RECENT PROJECTS AND ITERATIONS</div>
        </div>
        <label className="search-box">
          <Search size={16} />
          <input
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </label>
      </div>

      {loading && historyItems.length === 0 ? (
        <LoadingSpinner message="Searching audit and project records..." />
      ) : (
        <HistoryTable
          projects={historyItems}
          onSelectProject={handleSelect}
          totalCount={totalCount}
        />
      )}
    </div>
  )
}
