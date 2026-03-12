import { Outlet, Link, useLocation } from "react-router-dom";
import { useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";

/** Public site: professional layout inspired by chl.lk — logo, nav (Home, About, Quality, Contact), footer.
 * When on public site, clear admin auth so that clicking Admin always asks for username and password.
 */
export default function PublicLayout() {
  const location = useLocation();
  const { logout } = useAuth();

  useEffect(() => {
    logout();
  }, [logout]);

  const isActive = (path: string) => location.pathname === path || (path === "/" && location.pathname === "/");

  return (
    <div className="public-website-page">
      {/* Header: company logo + nav (Home, About, Quality, Contact) in the middle */}
      <header className="public-header">
        <div className="public-header-inner">
          <Link to="/" className="public-logo">
            <img src="/company-logo.png" alt="Ceylon Coco Pure Water" className="public-logo-img" />
          </Link>
          <nav className="public-nav-bar" aria-label="Main">
            <Link to="/" className={isActive("/") ? "active" : ""}>HOME</Link>
            <Link to="/about" className={isActive("/about") ? "active" : ""}>ABOUT</Link>
            <Link to="/quality" className={isActive("/quality") ? "active" : ""}>QUALITY</Link>
            <Link to="/contact" className={isActive("/contact") ? "active" : ""}>CONTACT</Link>
          </nav>
          <Link to="/admin" className="public-nav-admin">Admin</Link>
        </div>
      </header>

      <main className="public-main">
        <div className="public-page-content">
          <Outlet />
        </div>
      </main>

      {/* Footer — like chl.lk: Office, Factory, hours, copyright */}
      <footer className="public-footer">
        <div className="public-footer-inner">
          <div className="public-footer-grid">
            <div>
              <h3>Ceylon Coco</h3>
              <p>E-Tongue authenticity &amp; ingredient transparency for coconut water.</p>
            </div>
            <div>
              <h4>Office</h4>
              <p>12 ABC Drive, Colombo 3, Sri Lanka</p>
            </div>
            <div>
              <h4>Factory</h4>
              <p>ABC drive, Sri Lanka</p>
            </div>
            <div>
              <h4>Contact</h4>
              <p>+947712345678</p>
              <p><a href="mailto:transparency@ceyloncoco.lk">transparency@ceyloncoco.lk</a></p>
            </div>
          </div>
          <div className="public-footer-links">
            <Link to="/">Home</Link>
            <Link to="/about">About</Link>
            <Link to="/quality">Quality</Link>
            <Link to="/contact">Contact</Link>
          </div>
          <p className="public-footer-copy">© {new Date().getFullYear()} Ceylon Coco — Transparency. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
