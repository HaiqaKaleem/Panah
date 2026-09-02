import blueprintImg from '../../assets/blueprint.png'

export default function StandardsContent({ ruleDetail }) {
  const title = ruleDetail?.name || ruleDetail?.title || '2.2 Structural Stability'
  const description = ruleDetail?.description || (
    'Shelters and settlements must provide a secure and healthy living environment with adequate privacy, dignity, and protection from the climate, while supporting daily activities.'
  )

  const keyActions = ruleDetail?.key_actions || [
    {
      num: '1',
      title: 'Assess structural hazards',
      body: 'Identify and mitigate risks from natural hazards (e.g., earthquakes, floods, high winds) during site selection and construction. Ensure existing structures are assessed for safety before occupation.',
    },
    {
      num: '2',
      title: 'Use appropriate materials',
      body: 'Select building materials and construction techniques that are culturally acceptable, climate-appropriate, and technically sound. Prioritize local materials where sustainable.',
    },
  ]

  const indicators = ruleDetail?.indicators || [
    {
      name: 'Wind Load Resistance',
      threshold: '> 120 km/h sustained (ASCE 7 Exposure C)',
      source: 'Engineering sign-off / Field testing',
    },
    {
      name: 'Snow Load Capacity (Alpine)',
      threshold: '> 50 kg/m²',
      source: 'Visual inspection / Rafter span calcs',
    },
    {
      name: 'Lifespan of Emergency Shelter',
      threshold: 'Minimum 6 months (Extendable to 2+ years)',
      source: 'Material procurement logs / Post-distribution monitoring',
    },
  ]

  return (
    <section className="card std-content">
      <h1 className="std-title">{title}</h1>
      <blockquote>{description}</blockquote>

      <div className="std-section-head">
        <span className="k-badge">K</span>
        <h2>Key Actions</h2>
      </div>
      {keyActions.map((action, idx) => (
        <div className="action-box" key={idx}>
          <div className="action-title">
            <span className="num">{action.num || idx + 1}</span> {action.title}
          </div>
          <p>{action.body || action.description}</p>
        </div>
      ))}

      <div className="std-section-head">
        <span className="k-badge">I</span>
        <h2>Technical Indicators</h2>
      </div>
      <table className="std-table">
        <thead>
          <tr>
            <th>INDICATOR</th>
            <th>TARGET THRESHOLD</th>
            <th>VERIFICATION SOURCE</th>
          </tr>
        </thead>
        <tbody>
          {indicators.map((ind, idx) => (
            <tr key={idx}>
              <td>{ind.name || ind.indicator}</td>
              <td className="serif">{ind.threshold || ind.target_threshold}</td>
              <td>{ind.source || ind.verification_source}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <div className="std-figure">
        <img src={blueprintImg} alt="Shelter design technical drawings" />
        <div className="std-tooltip">
          <div className="std-tooltip-title">Cross-bracing requirements</div>
          <p>
            Adequate cross-bracing in both wall planes is mandatory to resist lateral wind loads. Refer to structural calculation matrix for material-specific sizing.
          </p>
        </div>
      </div>
    </section>
  )
}
