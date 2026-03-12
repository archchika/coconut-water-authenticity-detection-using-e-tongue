import { Link } from "react-router-dom";

/**
 * Public home page — hero and ingredient transparency. Measurement details (graphs, KPIs) are on the Quality page only.
 */
export default function PublicDashboard() {
  return (
    <div className="public-dashboard">
      <section className="public-hero">
        <img src="/hero.jpg" alt="Fresh green coconuts with splashing water" className="public-hero-img" />
        <div className="public-hero-overlay">
          <h1>Smart Coconut Authenticity &amp; Quality Analysis Platform</h1>
          <p>E-Tongue authenticity &amp; ingredient estimates — see <Link to="/quality">Quality</Link> for measurement details</p>
        </div>
      </section>

      <section className="public-welcome-section">
        <p className="public-welcome-label">Welcome to</p>
        <h2 className="public-welcome-company">Ceylon Coco (Pvt) Ltd</h2>
        <p className="public-welcome-body">
          Founded with a passion for natural wellness, Ceylon Coco (Pvt) Ltd was established to deliver premium-quality Sri Lankan king coconut water to local and international markets.
        </p>
        <p className="public-welcome-body">
          Our state-of-the-art processing facility ensures hygienic extraction, advanced filtration, and quality-controlled packaging to preserve the natural taste, nutrients, and freshness of every coconut.
        </p>
        <p className="public-welcome-body public-welcome-body--intro">We specialize in</p>
        <ul className="public-welcome-list">
          <li>100% Natural Coconut Water</li>
          <li>Organic Coconut-Based Beverages</li>
          <li>Value-Added Coconut Products</li>
        </ul>
        <p className="public-welcome-body">
          At Ceylon Coco, we combine traditional harvesting methods with modern scientific testing technology to ensure purity, authenticity, and superior quality.
        </p>
        <h3 className="public-welcome-subhead">We are committed to the highest standards of<br />Quality &amp; Food Safety Excellence</h3>
        <p className="public-welcome-body">
          As a responsible supplier to the global marketplace, we prioritize safety, sustainability, and transparency in everything we do.
        </p>
        <p className="public-welcome-body public-welcome-body--intro">Our production processes are designed to</p>
        <ul className="public-welcome-list">
          <li>Maintain natural pH balance and electrolyte levels</li>
          <li>Ensure strict hygiene and contamination control</li>
          <li>Support environmentally friendly packaging</li>
          <li>Meet international export quality standards</li>
        </ul>
        <p className="public-welcome-body">
          We continuously invest in innovation and advanced testing systems including sensor-based quality verification to guarantee that every bottle of Ceylon Coco meets the highest standards of purity and freshness.
        </p>
        <p className="public-welcome-body">
          Our commitment is not only to produce safe and healthy beverages but also to protect the environment and support Sri Lankan coconut farmers.
        </p>
      </section>

      <section className="public-products-section public-products-section--same-height">
        <header className="public-products-header-block">
          <h2 className="public-products-header-title">Good taste starts here</h2>
          <p className="public-products-header-sub">Crack open our specialties</p>
        </header>
        <div className="public-products-grid public-products-grid--four">
          <div className="public-product-card">
            <img src="/model-2.png" alt="Ceylon Coco Organic Coconut Water" />
            <span className="public-product-caption">Organic coconut water 200ml</span>
          </div>
          <div className="public-product-card">
            <img src="/model-3.png" alt="Ceylon Coco Organic Coconut Water" />
            <span className="public-product-caption">Organic coconut water 330ml</span>
          </div>
          <div className="public-product-card">
            <img src="/screenshot-113110.png" alt="Ceylon Coco Organic Water" />
            <span className="public-product-caption">Organic coconut water 400ml</span>
          </div>
          <div className="public-product-card">
            <img src="/screenshot-113118.png" alt="Ceylon Coco Coconut Water" />
            <span className="public-product-caption">Organic coconut water 500ml</span>
          </div>
        </div>
      </section>
    </div>
  );
}
