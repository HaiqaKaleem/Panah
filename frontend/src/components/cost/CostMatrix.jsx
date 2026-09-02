import { SlidersHorizontal, Plus } from 'lucide-react'

export default function CostMatrix({ bomItems = [], onAddLogistics }) {
  // If backend BOM lines are present, map them; otherwise use standard catalog pricing
  const defaultItems = [
    { name: 'Bamboo Culms', qty: '4m x Qty 24', price: '$0.00', tone: 'free', tag: 'SITE SOURCED', tagTone: 'green' },
    { name: 'Recycled Corrugated Tin', qty: '12 sheets', price: '$4.50', tone: 'paid', tag: 'BAZAAR', tagTone: 'red' },
    { name: 'Steel Fasteners', qty: 'Qty 32', price: '$0.80', tone: 'mid', tag: 'NGO DEPOT', tagTone: 'gray' },
    { name: 'Mud Fill / Earth', qty: '3.5m³', price: '$0.00', tone: 'free', tag: 'ON-SITE', tagTone: 'green' },
    { name: 'Secondary Web Struts', qty: '2m x Qty 18', price: '$0.00', tone: 'free', tag: 'SITE SOURCED', tagTone: 'green' },
    { name: 'Corner Bracing Steel Plates', qty: 'Qty 16', price: '$1.20', tone: 'mid', tag: 'NGO DEPOT', tagTone: 'gray' },
  ]

  const displayItems = bomItems.length > 0
    ? bomItems.map((item) => {
        const isFree = (item.line_cost_usd || 0) === 0 || item.local_availability === 'on-site'
        const tag = item.local_availability === 'on-site'
          ? 'SITE SOURCED'
          : item.local_availability === 'regional'
          ? 'NGO DEPOT'
          : 'BAZAAR'
        const tagTone = tag === 'SITE SOURCED' ? 'green' : tag === 'NGO DEPOT' ? 'gray' : 'red'

        return {
          name: item.material_name || item.material_type || item.member_type || 'Component',
          qty: `${item.length_m ? `${item.length_m}m x ` : ''}Qty ${item.quantity || 1}`,
          price: isFree ? '$0.00' : `$${Number(item.line_cost_usd || 0).toFixed(2)}`,
          tone: isFree ? 'free' : (item.line_cost_usd > 3 ? 'paid' : 'mid'),
          tag,
          tagTone,
        }
      })
    : defaultItems

  return (
    <section className="card cost-card">
      <div className="cost-head">
        <h3>LOCAL MARKET COST MATRIX</h3>
        <SlidersHorizontal size={17} className="muted-icon" />
      </div>
      <div className="cost-items">
        {displayItems.map((item, i) => (
          <div className="cost-item" key={i}>
            <div className="cost-item-top">
              <span className="cost-name">{item.name}</span>
              <span className={`cost-price ${item.tone}`}>{item.price}</span>
            </div>
            <div className="cost-item-bottom">
              <span className="cost-qty">{item.qty}</span>
              <span className={`cost-tag ${item.tagTone}`}>{item.tag}</span>
            </div>
          </div>
        ))}
      </div>
      <button className="btn-logistics" onClick={onAddLogistics}>
        <Plus size={14} /> ADD LOGISTICS OVERHEAD
      </button>
    </section>
  )
}
