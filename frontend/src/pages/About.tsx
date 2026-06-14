import { Link } from "react-router-dom";
import aboutHeroImg from "../assets/about-hero.png";

/**
 * About page — company story and mission (inspired by chl.lk).
 */
export default function About() {
  return (
    <div className="public-about-page">
      <section className="public-hero public-hero-sub">
        <img src={aboutHeroImg} alt="Organic Ceylon Coco Coconut Water" className="public-hero-img" />
        <div className="public-hero-overlay">
          <h1>About Ceylon Coco</h1>
          <p>Authenticity &amp; transparency for coconut water</p>
        </div>
      </section>

      <section className="public-section public-about-story">
        <div className="public-two-col">
          <div className="public-two-col-media">
            <img src="/about-image.webp" alt="Coconut tree — Ceylon Coco" width="600" height="400" />
          </div>
          <div className="public-two-col-text">
            <h2>Our Story</h2>
            <p>
              Ceylon Coco was founded with a vision to preserve the natural heritage of Sri Lanka’s coconut industry while embracing modern technological innovation. Sri Lanka, historically known as <em>Ceylon</em>, has long been recognized worldwide for its rich coconut cultivation traditions, especially within the renowned Coconut Triangle region.
            </p>
            <p>
              Inspired by generations of local farmers who practiced sustainable coconut cultivation using traditional knowledge, Ceylon Coco aims to combine this agricultural heritage with advanced scientific and engineering solutions. Our journey began as an innovation-driven initiative focused on enhancing coconut product quality, authenticity, and safety through intelligent monitoring and automation technologies.
            </p>
          </div>
        </div>
        <div className="public-about-story-under">
          <p>
            With the growing global demand for natural and healthy coconut-based beverages and products, ensuring authenticity and quality has become increasingly important. Ceylon Coco was established to address this need by developing smart solutions capable of analyzing coconut water characteristics using modern sensing systems and machine learning technologies.
          </p>
          <p>
            Our mission is to support the coconut industry by promoting transparency, quality assurance, and sustainable processing methods while maintaining the natural nutritional value of coconut products. By integrating sensor technology, data analytics, and automation, Ceylon Coco contributes toward minimizing adulteration and improving consumer confidence in coconut-based products.
          </p>
          <p>
            Rooted in Sri Lankan values, we are committed to empowering local communities, supporting sustainable agricultural practices, and encouraging innovation within the coconut sector. Through research, technology development, and collaboration with industry stakeholders, Ceylon Coco strives to bridge traditional agriculture with the future of smart food quality assessment.
          </p>
          <p>
            At Ceylon Coco, we believe that innovation and sustainability together can protect the authenticity of nature’s most refreshing gift—the coconut.
          </p>
          <p>
            <Link to="/quality">Read about our quality &amp; methodology →</Link>
          </p>
        </div>
      </section>

      <section className="public-section public-about-vision-mission">
        <h2 className="public-about-vision-mission-title">Our Vision</h2>
        <p className="public-about-vision-mission-text">
          To lead the coconut water industry through innovation, quality excellence, and sustainable practices, bringing the freshness of Ceylon to the world.
        </p>
      </section>

      <section className="public-section public-about-vision-mission">
        <h2 className="public-about-vision-mission-title">Our Mission</h2>
        <p className="public-about-vision-mission-text">
          Our mission is to produce and deliver high-quality, organic coconut water that meets international standards while supporting local farmers and protecting the environment.
        </p>
        <ul className="public-about-mission-list">
          <li>To source premium coconuts from sustainable plantations in Sri Lanka.</li>
          <li>To ensure purity and authenticity through strict quality control processes.</li>
          <li>To maintain the natural nutritional value without artificial additives.</li>
          <li>To empower local communities and coconut farmers through fair partnerships.</li>
          <li>To adopt environmentally responsible manufacturing and packaging practices.</li>
          <li>To build long-term trust with customers through transparency and product excellence.</li>
        </ul>
      </section>
    </div>
  );
}
