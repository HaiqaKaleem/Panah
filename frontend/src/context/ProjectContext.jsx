import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { projectsApi } from '../api/projects'
import { sitesApi } from '../api/sites'
import { designApi } from '../api/design'

const ProjectContext = createContext(null)

export const DEFAULT_CONSTRAINTS = {
  schema_version: '1.0.0',
  version: 'CS-AUTO-01',
  occupancy: { people: 5 },
  site: { length_m: 6.0, width_m: 5.0 },
  materials: [
    {
      id: 'MAT-BAM-01',
      type: 'treated_bamboo',
      qty: 120,
      length_m: 3.0,
      diameter_m: 0.08,
    },
    {
      id: 'MAT-STL-43',
      type: 'steel_connector',
      qty: 48,
      length_m: 0.2,
      diameter_m: 0.02,
    },
    {
      id: 'MAT-ROF-02',
      type: 'corrugated_tin',
      qty: 24,
      length_m: 2.0,
      diameter_m: 0.01,
    },
    {
      id: 'MAT-FND-SLT',
      type: 'stabilized_mud_brick',
      qty: 100,
      length_m: 0.3,
      diameter_m: 0.15,
    },
  ],
  environment: { scenario: 'semi-arid, high wind zone' },
  design_target: 'roof_truss',
  unknowns: [],
}

export function ProjectProvider({ children }) {
  const [projects, setProjects] = useState([])
  const [activeProject, setActiveProject] = useState(null)
  const [sites, setSites] = useState([])
  const [activeSite, setActiveSite] = useState(null)
  const [constraintSet, setConstraintSet] = useState(DEFAULT_CONSTRAINTS)
  const [activeConstraintSetId, setActiveConstraintSetId] = useState(null)
  const [generatedDesigns, setGeneratedDesigns] = useState([])
  const [activeDesign, setActiveDesign] = useState(null)
  const [activeGeometry, setActiveGeometry] = useState(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState(null)

  // Fetch full details and 3D geometry for a specific design
  const loadDesignDetails = useCallback(async (projectId, siteId, designId) => {
    try {
      const [detail, geom] = await Promise.allSettled([
        designApi.getGeneratedDesign(projectId, siteId, designId),
        designApi.getGeometry(projectId, siteId, designId),
      ])

      const designData = detail.status === 'fulfilled' ? detail.value : null
      const geometryData = geom.status === 'fulfilled' ? geom.value : null

      setActiveDesign(designData)
      setActiveGeometry(geometryData)
    } catch (err) {
      console.warn('Failed to load design detail/geometry:', err)
    }
  }, [])

  // Initialize or load a specific project
  const loadProjectData = useCallback(async (project) => {
    if (!project) return
    setActiveProject(project)
    setLoading(true)

    try {
      // 1. Get or create site
      let siteList = await sitesApi.list(project.id)
      let currentSite = null

      if (!siteList || siteList.length === 0) {
        // Create initial default site
        currentSite = await sitesApi.create(project.id, {
          name: `${project.name} - Primary Site`,
          latitude: 33.6844,
          longitude: 73.0479,
          soil_type: 'clay_loam',
          hazard_zone: 'Zone 4',
        })
        siteList = [currentSite]
      } else {
        currentSite = siteList[0]
      }
      setSites(siteList)
      setActiveSite(currentSite)

      // 2. Get constraint sets
      const csList = await designApi.listConstraintSets(project.id, currentSite.id)
      let currentCsId = null

      if (!csList || csList.length === 0) {
        // Create initial default constraint set
        const createdCs = await designApi.createConstraintSet(project.id, currentSite.id, DEFAULT_CONSTRAINTS)
        currentCsId = createdCs.id
        setConstraintSet(DEFAULT_CONSTRAINTS)
      } else {
        currentCsId = csList[0].id
        setConstraintSet(csList[0].constraint_json || DEFAULT_CONSTRAINTS)
      }
      setActiveConstraintSetId(currentCsId)

      // 3. Get or generate designs
      let designs = await designApi.listGeneratedDesigns(project.id, currentSite.id)
      if (!designs || designs.length === 0) {
        designs = await designApi.generateDesigns(project.id, currentSite.id, currentCsId, 2)
      }
      setGeneratedDesigns(designs || [])

      if (designs && designs.length > 0) {
        await loadDesignDetails(project.id, currentSite.id, designs[0].id)
      }
      setError(null)
    } catch (err) {
      console.error('Error loading project data:', err)
      setError(err.message || 'Failed to load project details')
    } finally {
      setLoading(false)
    }
  }, [loadDesignDetails])

  // Initial load: Fetch all projects or create a starter one
  const refreshProjects = useCallback(async () => {
    setLoading(true)
    try {
      let list = await projectsApi.list()
      if (!list || list.length === 0) {
        // Seed an initial demo project if database is completely empty
        const initial = await projectsApi.create({
          name: 'Panah Shelter Prototype Alpha',
          location: 'Mindanao, Philippines',
          description: 'Emergency modular shelter system for monsoon and seismic recovery',
        })
        list = [initial]
      }
      setProjects(list)

      // Auto-select active project if none selected yet
      if (!activeProject && list.length > 0) {
        await loadProjectData(list[0])
      }
    } catch (err) {
      console.error('Failed to load projects list:', err)
      setError(err.message || 'Unable to connect to backend')
    } finally {
      setLoading(false)
    }
  }, [activeProject, loadProjectData])

  useEffect(() => {
    refreshProjects()
  }, [refreshProjects])

  // Switch to a project by ID
  const selectProject = async (projectId) => {
    const target = projects.find((p) => p.id === projectId)
    if (target) {
      await loadProjectData(target)
    }
  }

  // Create a brand new project
  const createNewProject = async ({ name, location, description }) => {
    setLoading(true)
    try {
      const newProj = await projectsApi.create({
        name: name || 'New Humanitarian Shelter',
        location: location || 'South Asia Regional Site',
        description: description || 'Generative structural design',
      })
      setProjects((prev) => [newProj, ...prev])
      await loadProjectData(newProj)
      return newProj
    } catch (err) {
      setError(err.message || 'Failed to create project')
      throw err
    } finally {
      setLoading(false)
    }
  }

  // Select a generated design candidate
  const selectDesign = async (designId) => {
    if (!activeProject || !activeSite) return
    await loadDesignDetails(activeProject.id, activeSite.id, designId)
  }

  // Generate new candidate designs with updated constraints
  const generateDesignsWithConstraints = async (newConstraints, count = 2) => {
    if (!activeProject || !activeSite) return
    setGenerating(true)
    setError(null)
    try {
      // 1. Create new constraint set record
      const updatedCsPayload = {
        ...constraintSet,
        ...newConstraints,
        version: `CS-${Date.now().toString().slice(-4)}`,
      }
      const csRecord = await designApi.createConstraintSet(activeProject.id, activeSite.id, updatedCsPayload)
      setActiveConstraintSetId(csRecord.id)
      setConstraintSet(updatedCsPayload)

      // 2. Generate designs
      const newDesigns = await designApi.generateDesigns(activeProject.id, activeSite.id, csRecord.id, count)
      setGeneratedDesigns(newDesigns)

      if (newDesigns && newDesigns.length > 0) {
        await loadDesignDetails(activeProject.id, activeSite.id, newDesigns[0].id)
      }
      return newDesigns
    } catch (err) {
      console.error('Generation failed:', err)
      setError(err.message || 'Generation failed')
      throw err
    } finally {
      setGenerating(false)
    }
  }

  // Run validation on active design
  const validateActiveDesign = async () => {
    if (!activeProject || !activeSite || !activeDesign) return
    try {
      const valResult = await designApi.validateDesign(activeProject.id, activeSite.id, activeDesign.id)
      // Refresh design detail
      await loadDesignDetails(activeProject.id, activeSite.id, activeDesign.id)
      return valResult
    } catch (err) {
      setError(err.message || 'Validation failed')
      throw err
    }
  }

  // Promote active design
  const promoteActiveDesign = async () => {
    if (!activeProject || !activeSite || !activeDesign) return
    try {
      const res = await designApi.promoteDesign(activeProject.id, activeSite.id, activeDesign.id)
      await loadDesignDetails(activeProject.id, activeSite.id, activeDesign.id)
      return res
    } catch (err) {
      setError(err.message || 'Promotion failed')
      throw err
    }
  }

  return (
    <ProjectContext.Provider
      value={{
        projects,
        activeProject,
        sites,
        activeSite,
        constraintSet,
        activeConstraintSetId,
        generatedDesigns,
        activeDesign,
        activeGeometry,
        loading,
        generating,
        error,
        refreshProjects,
        selectProject,
        createNewProject,
        selectDesign,
        generateDesignsWithConstraints,
        validateActiveDesign,
        promoteActiveDesign,
        setConstraintSet,
      }}
    >
      {children}
    </ProjectContext.Provider>
  )
}

export function useProject() {
  const context = useContext(ProjectContext)
  if (!context) {
    throw new Error('useProject must be used within a ProjectProvider')
  }
  return context
}
