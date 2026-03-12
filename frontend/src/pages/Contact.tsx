import { useState, FormEvent } from "react";

/**
 * Contact page — address, phone, email + contact form (inspired by chl.lk).
 */
export default function Contact() {
  const [submitted, setSubmitted] = useState(false);
  const [formData, setFormData] = useState({ fullName: "", phone: "", email: "", message: "" });

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSubmitted(true);
    setFormData({ fullName: "", phone: "", email: "", message: "" });
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <div className="public-contact-page">
      <section className="public-hero public-hero-sub">
        <div className="public-hero-solid">
          <h1>Contact Us</h1>
          <p>Get in touch for inquiries on authenticity and transparency</p>
        </div>
      </section>

      <section className="public-contact-form-section">
        <div className="public-contact-form-wrapper">
          <h2 className="public-contact-form-title">Contact Form</h2>
          {submitted ? (
            <p className="public-contact-form-success">Thank you. Your message has been sent.</p>
          ) : (
            <form className="public-contact-form" onSubmit={handleSubmit}>
              <input
                type="text"
                name="fullName"
                placeholder="Full Name"
                value={formData.fullName}
                onChange={handleChange}
                className="public-contact-form-input"
                required
              />
              <input
                type="tel"
                name="phone"
                placeholder="Phone"
                value={formData.phone}
                onChange={handleChange}
                className="public-contact-form-input"
              />
              <input
                type="email"
                name="email"
                placeholder="Email Address"
                value={formData.email}
                onChange={handleChange}
                className="public-contact-form-input"
                required
              />
              <textarea
                name="message"
                placeholder="Message"
                value={formData.message}
                onChange={handleChange}
                className="public-contact-form-textarea"
                rows={5}
                required
              />
              <button type="submit" className="public-contact-form-submit">
                SUBMIT MESSAGE
              </button>
            </form>
          )}
        </div>
      </section>

      <section className="public-section">
        <div className="public-contact-grid">
          <div className="dashboard-card public-contact-card">
            <h3>Office</h3>
            <p>Ceylon Coco (Pvt) Ltd</p>
            <p>12 ABC Drive, Colombo 3, Sri Lanka</p>
          </div>
          <div className="dashboard-card public-contact-card">
            <h3>Factory</h3>
            <p>ABC drive, Sri Lanka</p>
            <p>Dankotuwa, Sri Lanka</p>
          </div>
          <div className="dashboard-card public-contact-card">
            <h3>Phone</h3>
            <p><a href="tel:+947712345678">+947712345678</a></p>
          </div>
          <div className="dashboard-card public-contact-card">
            <h3>Email</h3>
            <p><a href="mailto:transparency@ceyloncoco.lk">transparency@ceyloncoco.lk</a></p>
          </div>
        </div>
      </section>

      <section className="public-section public-section-alt">
        <h2>More Inquiries</h2>
        <p>
          For product authenticity reports, calibration inquiries, or partnership, please use the contact details above or the form.
        </p>
      </section>
    </div>
  );
}
