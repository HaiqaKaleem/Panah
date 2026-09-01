import { useEffect, useRef, useState, useCallback } from 'react'
import * as THREE from 'three'
import { RotateCw, ZoomIn, ZoomOut, Eye, RefreshCw, Box } from 'lucide-react'

const TYPE_COLORS = {
  rafter: 0xff9800,
  beam: 0x4caf50,
  tie_beam: 0x4caf50,
  brace: 0x2196f3,
  strut: 0x2196f3,
  king_post: 0x9c27b0,
  column: 0x9c27b0,
  panel: 0x607d8b,
}

function createCylinder(group, p1, p2, radius, material) {
  const dir = new THREE.Vector3().subVectors(p2, p1)
  const len = dir.length()
  const geo = new THREE.CylinderGeometry(radius, radius, len, 12)
  const mesh = new THREE.Mesh(geo, material)
  mesh.position.copy(new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5))
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize())
  group.add(mesh)
}

function createDefaultTruss(group) {
  const span = 6
  const height = 2.2

  const pA = new THREE.Vector3(0, 0, 0)
  const pB = new THREE.Vector3(span, 0, 0)
  const pApex = new THREE.Vector3(span / 2, height, 0)

  const matRafter = new THREE.MeshStandardMaterial({ color: 0xff9800, roughness: 0.5 })
  const matTie = new THREE.MeshStandardMaterial({ color: 0x4caf50, roughness: 0.5 })
  const matWeb = new THREE.MeshStandardMaterial({ color: 0x2196f3, roughness: 0.5 })

  // Build front & back trusses + purlins
  for (let z = 0; z <= 4; z += 2) {
    const gA = pA.clone().setZ(z)
    const gB = pB.clone().setZ(z)
    const gApex = pApex.clone().setZ(z)

    createCylinder(group, gA, gApex, 0.05, matRafter)
    createCylinder(group, gB, gApex, 0.05, matRafter)
    createCylinder(group, gA, gB, 0.05, matTie)

    // Web braces
    const gMid = new THREE.Vector3(span / 2, 0, z)
    createCylinder(group, gApex, gMid, 0.04, matWeb)
    createCylinder(group, gA.clone().lerp(gApex, 0.5), gMid, 0.035, matWeb)
    createCylinder(group, gB.clone().lerp(gApex, 0.5), gMid, 0.035, matWeb)
  }

  // Longitudinal Ridge & Wall Purlins
  createCylinder(group, pApex.clone().setZ(0), pApex.clone().setZ(4), 0.06, matRafter)
  createCylinder(group, pA.clone().setZ(0), pA.clone().setZ(4), 0.06, matTie)
  createCylinder(group, pB.clone().setZ(0), pB.clone().setZ(4), 0.06, matTie)
}

export default function Viewport3D({ geometryData, activeDesignName = 'Module Alpha - 1', modelId = 'TSU-SH-042-B' }) {
  const mountRef = useRef(null)
  const sceneRef = useRef(null)
  const rendererRef = useRef(null)
  const cameraRef = useRef(null)
  const modelGroupRef = useRef(null)
  const frameIdRef = useRef(null)

  const [autoRotate, setAutoRotate] = useState(false)
  const [wireframe, setWireframe] = useState(false)
  const [showNodes, setShowNodes] = useState(true)

  // Drag rotation state
  const isDraggingRef = useRef(false)
  const prevMouseRef = useRef({ x: 0, y: 0 })

  const autoRotateRef = useRef(autoRotate)
  useEffect(() => {
    autoRotateRef.current = autoRotate
  }, [autoRotate])

  // Build 3D Truss Objects from Geometry Data
  const buildGeometry = useCallback(() => {
    const modelGroup = modelGroupRef.current
    if (!modelGroup) return

    // Clear previous models
    while (modelGroup.children.length > 0) {
      const obj = modelGroup.children[0]
      modelGroup.remove(obj)
      if (obj.geometry) obj.geometry.dispose()
      if (obj.material) {
        if (Array.isArray(obj.material)) obj.material.forEach((m) => m.dispose())
        else obj.material.dispose()
      }
    }

    if (!geometryData || !geometryData.nodes) {
      // Default parametric truss if no geometry data yet
      createDefaultTruss(modelGroup)
      return
    }

    // Convert nodes to array format whether it's an object or array
    const nodeList = Array.isArray(geometryData.nodes)
      ? geometryData.nodes
      : Object.entries(geometryData.nodes).map(([id, pt]) => ({
          id,
          x: pt.x || 0,
          y: pt.y || 0,
          z: pt.z || 0,
        }))

    if (nodeList.length === 0) {
      createDefaultTruss(modelGroup)
      return
    }

    const nodeMap = new Map()
    nodeList.forEach((n) => {
      nodeMap.set(n.id, new THREE.Vector3(n.x || 0, n.y || 0, n.z || 0))
    })

    // Calculate center for orbital alignment
    const center = new THREE.Vector3()
    nodeList.forEach((n) => {
      const pos = nodeMap.get(n.id)
      if (pos) center.add(pos)
    })
    center.divideScalar(nodeList.length)
    if (cameraRef.current) {
      cameraRef.current.lookAt(center)
    }

    // Render Nodes (Spheres)
    if (showNodes) {
      const nodeGeo = new THREE.SphereGeometry(0.08, 16, 16)
      const nodeMat = new THREE.MeshStandardMaterial({
        color: 0x00ffcc,
        emissive: 0x005544,
        roughness: 0.3,
        metalness: 0.8,
      })

      nodeList.forEach((n) => {
        const mesh = new THREE.Mesh(nodeGeo, nodeMat)
        const pos = nodeMap.get(n.id)
        if (pos) {
          mesh.position.copy(pos)
          modelGroup.add(mesh)
        }
      })
    }

    // Render Members (Cylinders)
    if (geometryData.members && Array.isArray(geometryData.members)) {
      geometryData.members.forEach((m) => {
        let p1 = null
        let p2 = null

        // If start is an object with x, y, z
        if (m.start && typeof m.start === 'object' && typeof m.start.x === 'number') {
          p1 = new THREE.Vector3(m.start.x, m.start.y, m.start.z)
        } else if (typeof m.start === 'string' && nodeMap.has(m.start)) {
          p1 = nodeMap.get(m.start)
        } else if (m.start_node && nodeMap.has(m.start_node)) {
          p1 = nodeMap.get(m.start_node)
        }

        // If end is an object with x, y, z
        if (m.end && typeof m.end === 'object' && typeof m.end.x === 'number') {
          p2 = new THREE.Vector3(m.end.x, m.end.y, m.end.z)
        } else if (typeof m.end === 'string' && nodeMap.has(m.end)) {
          p2 = nodeMap.get(m.end)
        } else if (m.end_node && nodeMap.has(m.end_node)) {
          p2 = nodeMap.get(m.end_node)
        }

        if (!p1 || !p2) return

        const dir = new THREE.Vector3().subVectors(p2, p1)
        const len = dir.length()
        if (len < 0.001) return

        const color = TYPE_COLORS[m.type] || 0x8b7355
        const radius = Math.max(0.03, (m.diameter || m.diameter_m || 0.08) / 2)

        const memberGeo = new THREE.CylinderGeometry(radius, radius, len, 12)
        const memberMat = new THREE.MeshStandardMaterial({
          color,
          roughness: 0.6,
          metalness: 0.2,
          wireframe,
        })

        const memberMesh = new THREE.Mesh(memberGeo, memberMat)
        const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5)
        memberMesh.position.copy(mid)
        memberMesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize())

        modelGroup.add(memberMesh)
      })
    }
  }, [geometryData, showNodes, wireframe])

  useEffect(() => {
    if (!mountRef.current) return

    const container = mountRef.current
    const width = container.clientWidth || 600
    const height = container.clientHeight || 380

    // 1. Scene
    const scene = new THREE.Scene()
    scene.background = new THREE.Color('#0c120f')
    sceneRef.current = scene

    // 2. Camera
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000)
    camera.position.set(8, 6, 10)
    camera.lookAt(3, 1.5, 2.5)
    cameraRef.current = camera

    // 3. Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    rendererRef.current = renderer

    container.innerHTML = ''
    container.appendChild(renderer.domElement)

    // 4. Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.7)
    scene.add(ambientLight)

    const dirLight1 = new THREE.DirectionalLight(0xffffff, 0.9)
    dirLight1.position.set(10, 20, 10)
    dirLight1.castShadow = true
    scene.add(dirLight1)

    const dirLight2 = new THREE.DirectionalLight(0x2e7d46, 0.4)
    dirLight2.position.set(-10, -10, -10)
    scene.add(dirLight2)

    // 5. Ground Grid
    const grid = new THREE.GridHelper(20, 20, 0x2e7d46, 0x1f3026)
    grid.position.y = 0
    scene.add(grid)

    // 6. Model Group
    const modelGroup = new THREE.Group()
    scene.add(modelGroup)
    modelGroupRef.current = modelGroup

    // Initial geometry build
    buildGeometry()

    // Animation Loop
    const animate = () => {
      if (modelGroupRef.current && autoRotateRef.current) {
        modelGroupRef.current.rotation.y += 0.005
      }
      if (rendererRef.current && sceneRef.current && cameraRef.current) {
        rendererRef.current.render(sceneRef.current, cameraRef.current)
      }
      frameIdRef.current = requestAnimationFrame(animate)
    }
    animate()

    // Handle Resize
    const handleResize = () => {
      if (!container || !rendererRef.current || !cameraRef.current) return
      const w = container.clientWidth
      const h = container.clientHeight
      cameraRef.current.aspect = w / h
      cameraRef.current.updateProjectionMatrix()
      rendererRef.current.setSize(w, h)
    }
    window.addEventListener('resize', handleResize)

    return () => {
      window.removeEventListener('resize', handleResize)
      if (frameIdRef.current) cancelAnimationFrame(frameIdRef.current)
      renderer.dispose()
      if (container && renderer.domElement && container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement)
      }
    }
  }, [buildGeometry])

  // Pointer Drag Interaction
  const handlePointerDown = (e) => {
    isDraggingRef.current = true
    prevMouseRef.current = { x: e.clientX, y: e.clientY }
  }

  const handlePointerMove = (e) => {
    if (!isDraggingRef.current || !modelGroupRef.current) return
    const dx = e.clientX - prevMouseRef.current.x
    const dy = e.clientY - prevMouseRef.current.y

    modelGroupRef.current.rotation.y += dx * 0.01
    modelGroupRef.current.rotation.x += dy * 0.01

    prevMouseRef.current = { x: e.clientX, y: e.clientY }
  }

  const handlePointerUp = () => {
    isDraggingRef.current = false
  }

  const handleWheel = (e) => {
    if (!cameraRef.current) return
    e.preventDefault()
    const zoomFactor = e.deltaY > 0 ? 1.08 : 0.92
    cameraRef.current.position.multiplyScalar(zoomFactor)
  }

  // Zoom Controls
  const zoomIn = () => {
    if (cameraRef.current) cameraRef.current.position.multiplyScalar(0.85)
  }

  const zoomOut = () => {
    if (cameraRef.current) cameraRef.current.position.multiplyScalar(1.15)
  }

  const resetView = () => {
    if (cameraRef.current && modelGroupRef.current) {
      modelGroupRef.current.rotation.set(0, 0, 0)
      cameraRef.current.position.set(8, 6, 10)
      cameraRef.current.lookAt(3, 1.5, 2.5)
    }
  }

  useEffect(() => {
    buildGeometry()
  }, [buildGeometry])

  return (
    <section className="card viewport-card-container">
      <div className="viewport-head">
        <div className="vp-left">
          <span className="vp-active">VIEWPORT: ACTIVE (WEBGL 3D)</span>
          <span className="vp-sep" />
          <span className="vp-model">model_id: {modelId}</span>
        </div>
        <span className="vp-pill">{activeDesignName}</span>
      </div>

      <div className="viewport-body" style={{ position: 'relative', overflow: 'hidden' }}>
        <div
          ref={mountRef}
          className="vp-canvas-3d"
          style={{ width: '100%', height: '340px', cursor: 'grab' }}
          onPointerDown={handlePointerDown}
          onPointerMove={handlePointerMove}
          onPointerUp={handlePointerUp}
          onPointerLeave={handlePointerUp}
          onWheel={handleWheel}
        />

        <div className="vp-specs">
          <div className="vp-specs-title">Parametric Specifications</div>
          <p><strong>Primary:</strong> Treated Bamboo (Phyllostachys)</p>
          <p><strong>Joints:</strong> S335 Galvanized Connectors</p>
          <p><strong>Truss Type:</strong> King Post Warren Truss</p>
          {geometryData?.members && (
            <p><strong>Members Count:</strong> {geometryData.members.length} elements</p>
          )}
        </div>
      </div>

      <div className="viewport-toolbar">
        <button
          className={`tool-btn ${autoRotate ? 'active' : ''}`}
          onClick={() => setAutoRotate(!autoRotate)}
          title="Toggle Auto Rotation"
        >
          <RotateCw size={16} />
        </button>
        <button className="tool-btn" onClick={resetView} title="Reset Camera">
          <RefreshCw size={16} />
        </button>
        <span className="tool-sep" />
        <button className="tool-btn" onClick={zoomIn} title="Zoom In">
          <ZoomIn size={16} />
        </button>
        <button className="tool-btn" onClick={zoomOut} title="Zoom Out">
          <ZoomOut size={16} />
        </button>
        <span className="tool-sep" />
        <button
          className={`tool-btn ${wireframe ? 'active' : ''}`}
          onClick={() => setWireframe(!wireframe)}
          title="Toggle Wireframe"
        >
          <Box size={16} />
        </button>
        <button
          className={`tool-btn ${showNodes ? 'active' : ''}`}
          onClick={() => setShowNodes(!showNodes)}
          title="Toggle Joint Nodes"
        >
          <Eye size={16} />
        </button>
      </div>
    </section>
  )
}
